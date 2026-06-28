#!/bin/bash
# Render FlyChill video with tracks + visuals
# Usage: bash render-flychill.sh [num_loops]

set -e

NUM_LOOPS=${1:-3}
TRACKS_DIR=/workspace/flychill-tracks
VISUALS_DIR=/workspace/flychill-visuals
OUTPUT_DIR=/workspace/flychill-video-production
mkdir -p "$OUTPUT_DIR"

cd "$TRACKS_DIR"

echo "=== FlyChill Video Renderer ==="
echo "Loops: $NUM_LOOPS"
echo "Tracks dir: $TRACKS_DIR"
echo "Visuals dir: $VISUALS_DIR"
echo ""

# Get all MP3 files, sort by filename
TRACKS=(*.mp3)
TOTAL=${#TRACKS[@]}
echo "Found $TOTAL tracks"

if [ "$TOTAL" -eq 0 ]; then
    echo "ERROR: No MP3 files found in $TRACKS_DIR"
    exit 1
fi

# Concatenate tracks with loop count
echo ""
echo "=== Step 1: Concatenating tracks (loop $NUM_LOOPS times) ==="

# Build concat list file with NUM_LOOPS repeats
CONCAT_LIST="$OUTPUT_DIR/concat-list.txt"
> "$CONCAT_LIST"
for ((i=1; i<=NUM_LOOPS; i++)); do
    for track in "${TRACKS[@]}"; do
        echo "file '$TRACKS_DIR/$track'" >> "$CONCAT_LIST"
    done
done
echo "Concat list: $(wc -l < $CONCAT_LIST) entries"

# Concatenate with ffmpeg
CONCAT_MP3="$OUTPUT_DIR/concat.mp3"
ffmpeg -y -f concat -safe 0 -i "$CONCAT_LIST" \
    -c copy "$CONCAT_MP3" 2>&1 | tail -5

# Get total duration
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$CONCAT_MP3")
DURATION_MIN=$(echo "scale=2; $DURATION / 60" | bc)
echo "Total audio duration: $DURATION seconds = $DURATION_MIN minutes"

# Build video from visuals (one PNG per track, looped to fill duration)
echo ""
echo "=== Step 2: Building video from visuals ==="

# Create concat list for visuals matching audio track list
VISUAL_CONCAT="$OUTPUT_DIR/visual-concat.txt"
> "$VISUAL_CONCAT"
NUM_VISUALS=$(ls "$VISUALS_DIR"/*.png 2>/dev/null | wc -l)
TRACK_DUR_AVG=$(echo "scale=2; $DURATION / ($TOTAL * $NUM_LOOPS)" | bc)
echo "Average track duration: $TRACK_DUR_AVG seconds"
echo "Available visuals: $NUM_VISUALS"

# Use first N visuals (matching track count)
VISUAL_FILES=($(ls "$VISUALS_DIR"/*.png | sort))
NUM_USE=$TOTAL
if [ "$NUM_USE" -gt "$NUM_VISUALS" ]; then
    NUM_USE=$NUM_VISUALS
fi

for ((i=1; i<=NUM_LOOPS; i++)); do
    for ((j=0; j<NUM_USE; j++)); do
        echo "file '$VISUALS_DIR/$(basename ${VISUAL_FILES[$j]})'" >> "$VISUAL_CONCAT"
        echo "duration $TRACK_DUR_AVG" >> "$VISUAL_CONCAT"
    done
done

# Last visual needs extra entry to mark end
echo "file '$VISUALS_DIR/$(basename ${VISUAL_FILES[$((NUM_USE-1))]})'" >> "$VISUAL_CONCAT"
echo "Visual concat list: $(wc -l < $VISUAL_CONCAT) entries"

# Generate video from visuals
VIDEO_ONLY="$OUTPUT_DIR/video-only.mp4"
ffmpeg -y -f concat -safe 0 -i "$VISUAL_CONCAT" \
    -vsync vfr -pix_fmt yuv420p \
    -vf "scale=1920:1080" \
    -r 24 \
    "$VIDEO_ONLY" 2>&1 | tail -5

echo ""
echo "=== Step 3: Combining audio + video ==="
FINAL="$OUTPUT_DIR/flychill-final.mp4"
ffmpeg -y -i "$VIDEO_ONLY" -i "$CONCAT_MP3" \
    -c:v libx264 -preset medium -crf 23 \
    -c:a aac -b:a 192k \
    -shortest \
    -movflags +faststart \
    "$FINAL" 2>&1 | tail -5

echo ""
echo "=== DONE ==="
ls -lh "$FINAL"
echo "Duration: $(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $FINAL) seconds = $(echo "scale=2; $(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $FINAL) / 60" | bc) minutes"
