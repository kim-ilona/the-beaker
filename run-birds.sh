#!/bin/bash

# Ensure processes close when you stop the script
trap "pkill -P $$; exit" SIGINT SIGTERM EXIT

source /opt/homebrew/Caskroom/miniforge/base/etc/profile.d/conda.sh
conda activate birdnet

ARCHIVE_DIR="$HOME/BirdResults/AudioResults"
TEMP_DIR="$ARCHIVE_DIR/temp"
mkdir -p "$TEMP_DIR"

while true; do
  # Setup date and time stamps
  FILE_TIME=$(date "+%Y%m%d_%H%M%S")
  TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
  
  CLIP="$TEMP_DIR/recording_${FILE_TIME}.wav"
  CLEAN_CLIP="$TEMP_DIR/recording_${FILE_TIME}_clean.wav"
  
  # ==========================================
  # STEP 1: Record 15 seconds of audio
  # ==========================================
  ffmpeg -f avfoundation -i ":1" -t 15 -ar 48000 -ac 1 "$CLIP" -y 2>/dev/null

  if [ -f "$CLIP" ]; then
  
    # ==========================================
    # STEP 2: Denoise the audio & delete raw clip
    # ==========================================
    python3 ~/BirdResults/denoise.py "$CLIP" "$CLEAN_CLIP"
    rm -f "$CLIP"

    # ==========================================
    # STEP 4: Analyze with BirdNET (Min 65% conf)
    # ==========================================
    python3 -m birdnet_analyzer.analyze \
      --output "$TEMP_DIR" \
      --lat 43.65 --lon -79.38 \
      --week $(date +%V) \
      --min_conf 0.65 \
      "$CLEAN_CLIP" 2>/dev/null

    # Look for the exact file BirdNET generated
    RESULT="$TEMP_DIR/BirdNET_SelectionTable.txt"

    if [ -f "$RESULT" ]; then
      # Read the result file, skipping the header row
      while IFS=$'\t' read -r selection begin end common scientific code confidence rest; do
        
        # Check if the row actually has bird data
        if [ -n "$common" ] && [ -n "$confidence" ]; then
          
          # Convert the decimal to a clean whole number
          PCT=$(echo "$confidence" | awk '{printf "%.0f", $1 * 100}')

          # Save straight to birdlog.txt
          echo -e "$TIMESTAMP\t$common\t$PCT\t$scientific" >> ~/BirdResults/birdlog.txt

          # ==========================================
          # NEW STEP: "High Score" Audio Saving
          # ==========================================
          SAFE_NAME="${common// /_}"
          NEW_FILE_PATH="$ARCHIVE_DIR/${SAFE_NAME}_${PCT}.wav"
          
          # Look for an existing file for this bird that has a number at the end
          EXISTING_FILE=$(ls "$ARCHIVE_DIR/${SAFE_NAME}_"[0-9]*.wav 2>/dev/null | head -n 1)
          
          if [ -n "$EXISTING_FILE" ]; then
            # Extract the old percentage from the filename
            BASENAME=$(basename "$EXISTING_FILE" .wav)
            OLD_PCT="${BASENAME##*_}" # Grabs everything after the last underscore
            
            # If the new confidence is strictly higher than the old one, upgrade it
            if [ "$PCT" -gt "$OLD_PCT" ]; then
              rm -f "$EXISTING_FILE"
              cp -f "$CLEAN_CLIP" "$NEW_FILE_PATH"
            fi
          else
            # No file exists yet, so save this one as the baseline
            cp -f "$CLEAN_CLIP" "$NEW_FILE_PATH"
          fi
          
          # Clean up any un-numbered files from the previous script run just in case
          rm -f "$ARCHIVE_DIR/${SAFE_NAME}.wav" 2>/dev/null
          # ==========================================

        fi
        
      done < <(tail -n +2 "$RESULT")
      
      # Clean up the text result file so the next loop starts fresh
      rm -f "$RESULT"
    fi
  fi

  # ==========================================
  # STEP 3: Keep only 10 files in the temp folder
  # ==========================================
  ls -t "$TEMP_DIR"/*.wav 2>/dev/null | tail -n +11 | xargs -I {} rm -f "{}"

git add birdlog.txt
git commit -m "update log" && git push

done