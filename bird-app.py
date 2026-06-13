#!/usr/bin/env python3
import tkinter as tk
import subprocess
import os
import signal
import sys
import time
from datetime import datetime

BG     = "#0f1117"
CARD   = "#1a1f2e"
BORDER = "#1f2937"
WHITE  = "#f9fafb"
MUTED  = "#6b7280"
GREEN  = "#4ade80"
RED    = "#f87171"
BLUE   = "#1d4ed8"
FONT   = "Arial"

server_proc = None
mic_proc    = None

def kill_port():
    try:
        r = subprocess.run(["lsof", "-ti:8765"], capture_output=True, text=True)
        for pid in r.stdout.strip().split():
            try:
                os.kill(int(pid), signal.SIGKILL)
            except:
                pass
        time.sleep(0.5)
    except:
        pass

def start():
    global server_proc, mic_proc
    if mic_proc and mic_proc.poll() is None:
        return
    kill_port()
    BIRD_DIR = os.path.expanduser("~/BirdResults")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8765"],
        cwd=BIRD_DIR,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    mic_proc = subprocess.Popen(
        ["bash", os.path.expanduser("~/BirdResults/run-birds.sh")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid
    )
    status_dot.config(fg=GREEN)
    status_text.config(text="Listening...")
    poll()

def stop():
    global mic_proc, server_proc
    if mic_proc:
        try:
            os.killpg(os.getpgid(mic_proc.pid), signal.SIGTERM)
        except:
            try:
                mic_proc.terminate()
            except:
                pass
    if server_proc:
        try:
            server_proc.terminate()
        except:
            pass
    kill_port()
    status_dot.config(fg=RED)
    status_text.config(text="Stopped")

def open_dashboard():
    subprocess.Popen(["open", "http://localhost:8765/avian-visitors-dashboard.html"])

def on_close():
    stop()
    root.after(300, force_quit)

def force_quit():
    root.destroy()
    os.kill(os.getpid(), signal.SIGKILL)

def count_today():
    try:
        path = os.path.expanduser("~/BirdResults/birdlog.txt")
        today = datetime.now().strftime("%Y-%m-%d")
        with open(path) as f:
            return sum(1 for l in f if l.startswith(today))
    except:
        return 0

def poll():
    count_label.config(text=f"{count_today()} detections today")
    root.after(5000, poll)

# ── Window ──────────────────────────────────────────────
root = tk.Tk()
root.title("Bird Dashboard")
root.geometry("300x220")
root.resizable(False, False)
root.configure(bg=BG)
root.protocol("WM_DELETE_WINDOW", on_close)

# Title
tk.Label(root, text="🐦 Avian Visitor Monitor",
         font=(FONT, 13, "bold"), bg=BG, fg=WHITE).pack(pady=(18, 6))

# Status row
sf = tk.Frame(root, bg=CARD, bd=0, highlightthickness=1,
              highlightbackground=BORDER)
sf.pack(padx=60, pady=(0, 12), ipadx=10, ipady=4)
status_dot  = tk.Label(sf, text="●", font=(FONT, 12), bg=CARD, fg=MUTED)
status_dot.pack(side="left", padx=(8, 4))
status_text = tk.Label(sf, text="Idle", font=(FONT, 11), bg=CARD, fg=WHITE)
status_text.pack(side="left", padx=(0, 10))

# Divider
tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0, 14))

# Buttons
bf = tk.Frame(root, bg=BG)
bf.pack()

def btn(parent, text, fg, bg, cmd):
    b = tk.Button(parent, text=text, font=(FONT, 10, "bold"),
                  fg=fg, bg=bg, activebackground=bg, activeforeground=fg,
                  relief="flat", bd=0, padx=14, pady=7,
                  highlightthickness=1, highlightbackground=BORDER,
                  cursor="hand2", command=cmd)
    b.pack(side="left", padx=6)
    return b

btn(bf, "▶ Record",    GREEN, CARD, start)
btn(bf, "■ Stop",      RED,   CARD, stop)
btn(bf, "⤢ Dashboard", WHITE, BLUE, open_dashboard)

# Divider
tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(14, 8))

# Count
count_label = tk.Label(root, text="— detections today",
                       font=(FONT, 9), bg=BG, fg=MUTED)
count_label.pack()

poll()
root.mainloop()
