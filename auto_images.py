#!/usr/bin/env python3
import time
import subprocess
from pathlib import Path

LOG_FILE = Path.home() / "BirdResults" / "birdlog.txt"
GEN_SCRIPT = Path.home() / "BirdResults" / "generate_bird_image.py"

def get_unique_birds():
    if not LOG_FILE.exists():
        return set()
    birds = set()
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    birds.add(parts[1])
    except Exception as e:
        print(f"Error reading log: {e}")
    return birds

def main():
    print("🐦 Image Watcher Started!")
    print(f"Monitoring {LOG_FILE.name} for new species...")
    
    # Keep track of what we've processed this session
    processed = set()
    
    while True:
        current_birds = get_unique_birds()
        
        # Find birds in the log that we haven't processed yet
        new_birds = current_birds - processed
        
        for bird in new_birds:
            # Mark it as processed so we don't trigger it again in this loop
            processed.add(bird)
            
            # The generate_bird_image.py script handles skipping if the 
            # PNG is already cached in species_images.json, so this is safe!
            subprocess.run(["python3", str(GEN_SCRIPT), bird])
            
        time.sleep(5)

if __name__ == "__main__":
    main()
