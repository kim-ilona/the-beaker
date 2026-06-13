#!/bin/bash
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate birdnet

mkdir -p /tmp/birdtemp

while true; do
  # THIS IS THE CRITICAL FIX: Wipe the temp folder clean before recording
  rm -rf /tmp/birdtemp/*

  CLIP="/tmp/birdtemp/birdclip_$(date +%H%M%S).wav"
  CLEAN_CLIP="/tmp/birdtemp/birdclip_clean_$(date +%H%M%S).wav"
  TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

  # Record 15 seconds of audio
  ffmpeg -f avfoundation -i ":1" -t 15 -ar 48000 -ac 1 "$CLIP" -y 2>/dev/null

  if [ -f "$CLIP" ]; then
    # Always save the latest clip, regardless of detection
    cp "$CLIP" ~/BirdResults/AudioResults/latest.wav

    # Denoise the clip before analysis
    python3 ~/BirdResults/denoise.py "$CLIP" "$CLEAN_CLIP"

    # Analyze the denoised clip with BirdNET
    python3 -m birdnet_analyzer.analyze "$CLEAN_CLIP" \
      --output /tmp/birdtemp/ \
      --lat 43.65 --lon -79.38 \
      --week $(date +%V) \
      --min_conf 0.65 2>/dev/null

    RESULT=$(ls /tmp/birdtemp/*.txt 2>/dev/null | head -1)

    if [ -f "$RESULT" ]; then
      while IFS=$'\t' read -r selection begin end common scientific code confidence rest; do
        conf_val="${confidence:-0}"
        PCT=$(printf "%.0f" $(echo "$conf_val * 100" | bc -l 2>/dev/null || echo 0))

        if [ "$PCT" -ge 65 ]; then
          echo -e "$TIMESTAMP\t$common\t$PCT\t$scientific" >> ~/BirdResults/birdlog.txt

          SAFE_NAME="${common// /_}"
          cp "$CLIP" ~/BirdResults/AudioResults/"$SAFE_NAME.wav"
        fi
      done < <(tail -n +2 "$RESULT")
    fi
  fi

  echo "Analyzed at $TIMESTAMP"
done