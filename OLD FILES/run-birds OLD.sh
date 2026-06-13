#!/bin/bash
source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate birdnet

while true; do
  CLIP=~/BirdResults/birdclip_$(date +%H%M%S).wav
  TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
  ffmpeg -f avfoundation -i ":1" -t 15 -ar 48000 -ac 1 "$CLIP" -y 2>/dev/null
  
  if [ -f "$CLIP" ]; then
    python3 -m birdnet_analyzer.analyze "$CLIP" \
      --output /tmp/birdtemp/ \
      --lat 43.65 --lon -79.38 \
      --week $(date +%V) \
      --min_conf 0.4 2>/dev/null
      
    RESULT=$(ls /tmp/birdtemp/*.txt 2>/dev/null | head -1)
    
    if [ -f "$RESULT" ]; then
      tail -n +2 "$RESULT" | while IFS=$'\t' read -r selection begin end common scientific code confidence rest; do
        # Extract the confidence value, defaulting to 0 if empty
        conf_val="${confidence:-0}"
        
        # Calculate percentage
        PCT=$(printf "%.0f" $(echo "$conf_val * 100" | bc -l 2>/dev/null || echo 0))
        
        # Only log if PCT is >= X
        if [ "$PCT" -ge 40 ]; then
          echo -e "$TIMESTAMP\t$common\t$PCT\t$scientific" >> ~/BirdResults/birdlog.txt
        fi
      done
      # Clean up the processed result file so we don't read it again next loop
      rm -f "$RESULT"
    fi
    rm -f "$CLIP"
  fi
  echo "Analyzed at $TIMESTAMP"
done