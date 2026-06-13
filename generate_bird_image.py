#!/usr/bin/env python3
"""
generate_bird_image.py
Usage: python3 generate_bird_image.py "American Robin"
Generates a local image using mflux for a bird species, reading the prompt from prompt.txt.
"""

import sys
import json
import subprocess
from pathlib import Path

IMG_DIR = Path.home() / "BirdResults" / "images"
CACHE = Path.home() / "BirdResults" / "species_images.json"
PROMPT_FILE = Path.home() / "BirdResults" / "prompt.txt"

IMG_DIR.mkdir(parents=True, exist_ok=True)

def slug(name):
    return name.lower().replace(" ", "_").replace("'", "").replace("-", "_")

def load_cache():
    if CACHE.exists():
        with open(CACHE) as f:
            return json.load(f)
    return {}

def save_cache(data):
    with open(CACHE, "w") as f:
        json.dump(data, f, indent=2)

def generate(com_name):
    cache = load_cache()
    key = slug(com_name)

    if key in cache and Path(cache[key]).exists():
        print(f"[cache] {com_name} already exists: {cache[key]}")
        return cache[key]

    # Read the prompt from the text file
    with open(PROMPT_FILE, "r") as f:
        raw_prompt = f.read().strip()
    
    # Inject the bird's name into the prompt
    # If the user included {bird_name} in their text file, replace it.
    # Otherwise, just append the bird's name to the end.
    if "{bird_name}" in raw_prompt:
        final_prompt = raw_prompt.replace("{bird_name}", com_name)
    else:
        final_prompt = f"{raw_prompt} The bird species is: {com_name}"

    out_path = IMG_DIR / f"{key}.png"

    print(f"[generate] Running mflux locally for: {com_name}...")
    
    cmd = [
        "mflux-generate",
        "--prompt", final_prompt,
        "--output", str(out_path),
        "--model", "schnell",
        "--steps", "8",
        "--width", "1024",
        "--height", "1024",
        "-q", "8"
    ]

    try:
        subprocess.run(cmd, check=True)
        
        if out_path.exists():
            cache[key] = str(out_path)
            save_cache(cache)
            print(f"\n[saved] {out_path}")
            return str(out_path)
        else:
            print(f"\n[error] Output file not found: {out_path}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"\n[error] mflux-generate failed: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 generate_bird_image.py "Common Name"')
        sys.exit(1)
    com_name = " ".join(sys.argv[1:])
    result = generate(com_name)
    print(result if result else "FAILED")
