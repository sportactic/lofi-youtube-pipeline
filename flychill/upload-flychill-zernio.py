#!/usr/bin/env python3
"""Upload video to @FlyChill via Zernio API (NOT direct YouTube API).

Uses Zernio's media upload + post creation endpoints.
The video file must be uploaded first to get a public URL.

Steps:
1. Get presigned URL from Zernio
2. PUT video file to presigned URL
3. POST to /api/v1/posts with platform: youtube

Usage:
  python3 upload-flychill-zernio.py /path/to/video.mp4 "Video Title"
"""
import os, sys, json, subprocess
import requests

ZERNIO_API_KEY = os.environ['ZERNIO_API_KEY']
FLYCHILL_ACCOUNT_ID = os.environ.get('FLYCHILL_ZERNIO_ACCOUNT_ID', '6a4076bf9d9472faae0b16dc')

if len(sys.argv) < 2:
    print("Usage: upload-flychill-zernio.py <video.mp4> [title] [visibility]")
    sys.exit(1)

VIDEO_FILE = sys.argv[1]
TITLE = sys.argv[2] if len(sys.argv) > 2 else "FlyChill • 1 Hour+ Cozy Lofi Beats"
VISIBILITY = sys.argv[3] if len(sys.argv) > 3 else "public"

# Step 1: Get presigned URL
size = os.path.getsize(VIDEO_FILE)
print(f"Video: {VIDEO_FILE} ({size} bytes = {size/1024/1024:.1f} MB)")

print("\n=== Step 1: Get presigned URL ===")
presign_resp = requests.post(
    'https://zernio.com/api/v1/media/presign',
    headers={
        'Authorization': f'Bearer {ZERNIO_API_KEY}',
        'Content-Type': 'application/json',
    },
    json={
        'filename': os.path.basename(VIDEO_FILE),
        'contentType': 'video/mp4',
        'size': size,
    },
    timeout=60,
)
presign = presign_resp.json()
upload_url = presign['uploadUrl']
public_url = presign['publicUrl']
print(f"Public URL: {public_url}")

# Step 2: Upload to presigned URL
print("\n=== Step 2: Upload to R2 ===")
with open(VIDEO_FILE, 'rb') as f:
    put_resp = requests.put(upload_url, data=f, headers={'Content-Type': 'video/mp4'}, timeout=1800)
print(f"Upload HTTP: {put_resp.status_code}")

if put_resp.status_code != 200:
    print(f"Upload failed: {put_resp.text[:300]}")
    sys.exit(1)

# Step 3: Create post
print("\n=== Step 3: Create YouTube post ===")
description = """🎵 Welcome to FlyChill – your premium destination for lofi hip hop, chillhop, and relaxing aesthetic beats.

Perfect for: study, work, sleep, focus, relaxation.

🌙 FlyChill • Lofi • Chill • Chillhop
🔔 Subscribe and join the FlyChill community for daily lo-fi uploads.

#lofi #chillhop #chillout #lofihiphop #studymusic #sleepmusic #relaxingmusic"""

post_data = {
    'content': description,
    'title': TITLE,
    'mediaItems': [
        {'type': 'video', 'url': public_url}
    ],
    'platforms': [
        {
            'platform': 'youtube',
            'accountId': FLYCHILL_ACCOUNT_ID,
            'platformSpecificData': {
                'title': TITLE,
                'description': description,
                'visibility': VISIBILITY,
                'tags': ['lofi', 'chillhop', 'chillout', 'chill beats', 'study music', 
                         'sleep music', 'relaxing music', 'ambient', 'jazzy lofi', 
                         'lofi hip hop', 'flychill', 'cozy', 'rainy window', '1 hour']
            }
        }
    ],
    'publishNow': True,
}

post_resp = requests.post(
    'https://zernio.com/api/v1/posts',
    headers={
        'Authorization': f'Bearer {ZERNIO_API_KEY}',
        'Content-Type': 'application/json',
    },
    json=post_data,
    timeout=300,
)
result = post_resp.json()
print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])

# Find the YouTube URL
try:
    post = result.get('post', result)
    for p in post.get('platforms', []):
        if p.get('platform') == 'youtube':
            yt_url = p.get('platformPostUrl', 'not yet')
            print(f"\n✓ YouTube URL: {yt_url}")
except Exception as e:
    print(f"Error: {e}")
