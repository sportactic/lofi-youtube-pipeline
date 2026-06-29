#!/usr/bin/env bash
# Render 3 channels in parallel
set -e

CHANNELS=(
    "fly-chill:7b661a9c-107a-4297-b0ee-2fa015e66d8b"
    "lofi-nippon:2f6a96be-2327-4b87-baec-d21466d6d3c5"
    "thelofi:78136c59-6637-4eea-beba-9582e58b028d"
)

for CH in "${CHANNELS[@]}"; do
    CHANNEL="${CH%%:*}"
    PROJECT_ID="${CH##*:}"
    
    TRACKS_DIR="/workspace/tracks-${CHANNEL}-v3"
    VISUALS_DIR="/workspace/visuals-${CHANNEL}-v3"
    OUT_DIR="/workspace/v3-${CHANNEL}-prod"
    
    mkdir -p "$OUT_DIR"
    
    (
        echo "[$(date +%H:%M:%S)] === Starting $CHANNEL ==="
        
        # Determine loop count based on number of tracks
        NUM_TRACKS=$(ls $TRACKS_DIR/*.mp3 2>/dev/null | grep -v _metadata | wc -l)
        NUM_VISUALS=$(ls $VISUALS_DIR/*.png 2>/dev/null | wc -l)
        
        # Loop math: aim for 80-90 min video
        # 10 tracks: 3 loops = 80 min
        # 20 tracks: 2 loops = 90 min
        if [ "$NUM_TRACKS" -le 12 ]; then
            LOOPS=3
        else
            LOOPS=2
        fi
        
        echo "  Tracks: $NUM_TRACKS, Visuals: $NUM_VISUALS, Loops: $LOOPS"
        
        # Build audio concat (LOOPS * NUM_TRACKS entries)
        > $OUT_DIR/audio.txt
        for ((i=1; i<=LOOPS; i++)); do
            for f in $(ls $TRACKS_DIR/*.mp3 | grep -v _metadata | sort); do
                echo "file '$f'" >> $OUT_DIR/audio.txt
            done
        done
        echo "  Audio entries: $(wc -l < $OUT_DIR/audio.txt)"
        
        # Concat audio
        rm -f $OUT_DIR/audio.mp3
        ffmpeg -y -f concat -safe 0 -i $OUT_DIR/audio.txt -c copy $OUT_DIR/audio.mp3 2>&1 | tail -2
        AUDIO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $OUT_DIR/audio.mp3)
        echo "  Audio: ${AUDIO_DUR}s"
        
        # Build video concat (NUM_VISUALS * LOOPS entries, each visual = AUDIO_DUR/(NUM_VISUALS*LOOPS))
        PER_VISUAL=$(python3 -c "print($AUDIO_DUR / ($NUM_VISUALS * $LOOPS))")
        
        > $OUT_DIR/video.txt
        for ((i=1; i<=LOOPS; i++)); do
            for v in $(ls $VISUALS_DIR/*.png | sort); do
                echo "file '$v'" >> $OUT_DIR/video.txt
                echo "duration $PER_VISUAL" >> $OUT_DIR/video.txt
            done
        done
        echo "  Video entries: $(wc -l < $OUT_DIR/video.txt), per visual: ${PER_VISUAL}s"
        
        # Render video-only
        rm -f $OUT_DIR/video-only.mp4
        echo "  Rendering video-only..."
        ffmpeg -y -f concat -safe 0 -i $OUT_DIR/video.txt \
            -vsync vfr -pix_fmt yuv420p \
            -vf "scale=1280:720,fps=12" \
            -c:v libx264 -preset ultrafast -crf 28 \
            -movflags +faststart \
            $OUT_DIR/video-only.mp4 2>&1 | tail -3
        
        # Mux
        echo "  Muxing final..."
        rm -f $OUT_DIR/final.mp4
        ffmpeg -y -i $OUT_DIR/video-only.mp4 \
            -i $OUT_DIR/audio.mp3 \
            -c:v copy -c:a aac -b:a 192k \
            -shortest \
            -movflags +faststart \
            $OUT_DIR/final.mp4 2>&1 | tail -3
        
        FINAL_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $OUT_DIR/final.mp4 2>/dev/null)
        FINAL_SIZE=$(stat -c%s $OUT_DIR/final.mp4)
        echo "  ✓ Final: ${FINAL_DUR}s = $(python3 -c "print(round($FINAL_DUR/60, 2))")min, $((FINAL_SIZE/1024/1024))MB"
        echo ""
    ) > /tmp/render-$CHANNEL.log 2>&1 &
    
    echo "Started $CHANNEL render PID $!"
done

echo ""
echo "All 3 renders started in parallel"
echo "PIDs:"
ps -ef | grep "Rendering\|for CH in" | grep -v grep | head -10