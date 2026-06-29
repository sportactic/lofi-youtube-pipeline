#!/bin/bash
# Daily pipeline: render + end-screen + shorts + upload
# Called by cron at staggered times

set -e
CHANNEL=$1
LOOPS=$2
PUBLISH_AT=$3

if [ -z "$CHANNEL" ] || [ -z "$LOOPS" ] || [ -z "$PUBLISH_AT" ]; then
  echo "Usage: $0 <channel> <loops> <publish_at_iso>"
  exit 1
fi

echo "=== Daily pipeline: $CHANNEL ==="
echo "  Loops: $LOOPS"
echo "  Publish at: $PUBLISH_AT"

cd /workspace/daily-pipeline

# 1. Refresh Suno JWT
echo "  [1/6] Refreshing Suno JWT..."
node /workspace/.skills/suno-downloader/refresh-jwt.mjs 2>&1 | tail -1

# 2. Get tracks manifest
echo "  [2/6] Fetching tracks manifest..."
python3 get-tracks.py $CHANNEL

# 3. Apply seasonal content
echo "  [3/6] Detecting season..."
python3 seasonal-content.py 2>&1 | head -2

# 4. Render video
echo "  [4/6] Rendering video..."
python3 render.py $CHANNEL $LOOPS

# 5. Add end-screen
echo "  [5/6] Adding end-screen..."
python3 -c "
import sys; sys.path.insert(0, '/workspace/daily-pipeline')
from endscreen import create_end_screen, append_end_screen
create_end_screen('$CHANNEL', '/tmp/end-screen-$CHANNEL.mp4', duration=18)
append_end_screen('video-$CHANNEL.mp4', '/tmp/end-screen-$CHANNEL.mp4', 'video-$CHANNEL-final.mp4')
"
mv "video-$CHANNEL-final.mp4" "video-$CHANNEL-upload.mp4"

# 6. Upload
echo "  [6/6] Uploading..."
python3 upload-smart.py $CHANNEL video-$CHANNEL-upload.mp4 --publish-at "$PUBLISH_AT"

# 7. Generate 2 Shorts and upload
echo "  [+] Generating Shorts..."
python3 shorts-generator.py $CHANNEL video-$CHANNEL-upload.mp4 2 45
python3 shorts-uploader.py $CHANNEL shorts-$CHANNEL/short-01.mp4 shorts-$CHANNEL/short-02.mp4

echo "=== Done! ==="
