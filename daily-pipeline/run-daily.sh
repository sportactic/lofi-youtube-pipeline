#!/bin/bash
# Daily pipeline: render + upload 1 video per channel
# Called by cron at staggered times:
#   - thelofi: TR 22:00 (so video goes live at TR 22:00 next day)
#   - lofinippon: TR 04:00
#   - flychill: TR 10:00

set -e
CHANNEL=$1
LOOPS=$2  # 2 or 3
PUBLISH_AT=$3  # ISO 8601 UTC

if [ -z "$CHANNEL" ] || [ -z "$LOOPS" ] || [ -z "$PUBLISH_AT" ]; then
  echo "Usage: $0 <channel> <loops> <publish_at_iso>"
  exit 1
fi

echo "=== Daily pipeline: $CHANNEL ==="
echo "  Loops: $LOOPS"
echo "  Publish at: $PUBLISH_AT"

# 1. Refresh Suno JWT (so we get fresh tracks if any)
echo "  [1/5] Refreshing Suno JWT..."
node /workspace/.skills/suno-downloader/refresh-jwt.mjs 2>&1 | tail -3

# 2. Get tracks manifest
echo "  [2/5] Fetching tracks manifest..."
python3 /workspace/daily-pipeline/get-tracks.py $CHANNEL

# 3. Render video
echo "  [3/5] Rendering video..."
python3 /workspace/daily-pipeline/render.py $CHANNEL $LOOPS

# 4. Upload with smart title/description
echo "  [4/5] Uploading..."
python3 /workspace/daily-pipeline/upload-smart.py $CHANNEL \
  /workspace/daily-pipeline/video-$CHANNEL.mp4 \
  --publish-at "$PUBLISH_AT"

echo "  [5/5] Done!"
