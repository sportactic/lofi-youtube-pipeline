#!/usr/bin/env python3
"""Upload video to @FlyChill channel (UCvnQnOtZUJ9ZsM1ZgJpvBqQ).

Uses SEPARATE credentials from @The-Lo-Fi and @lofinippon:
- FLYCHILL_REFRESH_TOKEN
- FLYCHILL_CLIENT_SECRETS_JSON
- FLYCHILL_CHANNEL_ID

First video publishes IMMEDIATELY (no schedule). Subsequent videos can be scheduled.
"""
import os, sys, json, datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === FlyChill credentials ===
client_secrets = json.loads(os.environ['FLYCHILL_CLIENT_SECRETS_JSON'])
CLIENT_ID = client_secrets['installed']['client_id']
CLIENT_SECRET = client_secrets['installed']['client_secret']
REFRESH_TOKEN = os.environ['FLYCHILL_REFRESH_TOKEN']
CHANNEL_ID = os.environ['FLYCHILL_CHANNEL_ID']
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']

if REFRESH_TOKEN == 'PENDING_OAUTH_FLOW':
    print('ERROR: FLYCHILL_REFRESH_TOKEN is not yet set.', file=sys.stderr)
    print('Run oauth-flychill.py first to complete the OAuth flow.', file=sys.stderr)
    sys.exit(1)

creds = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    token_uri='https://oauth2.googleapis.com/token',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=SCOPES,
)

youtube = build('youtube', 'v3', credentials=creds)

print('=== Uploading to @FlyChill ===', file=sys.stderr)
print(f'Channel ID: {CHANNEL_ID}', file=sys.stderr)
print(f'Handle: {os.environ.get("FLYCHILL_CHANNEL_HANDLE", "@FlyChill")}', file=sys.stderr)

VIDEO_FILE = sys.argv[1] if len(sys.argv) > 1 else '/workspace/flychill-video-production/flychill-final.mp4'

# Schedule policy:
# - First video: publish IMMEDIATELY (default)
# - Subsequent: schedule at 22:00 UTC for US prime time
SCHEDULE = sys.argv[3] if len(sys.argv) > 3 else 'now'

if SCHEDULE == 'now':
    publish_at = None
    print('Mode: publish immediately', file=sys.stderr)
else:
    now = datetime.datetime.now(datetime.timezone.utc)
    target_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
    if now >= target_time:
        target_time = target_time + datetime.timedelta(days=1)
    publish_at = target_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    print(f'Mode: scheduled publish at {publish_at} UTC', file=sys.stderr)

# Default title matching existing FlyChill channel style
title = sys.argv[2] if len(sys.argv) > 2 else 'FlyChill • 1 Hour+ of Lofi Beats to Study Sleep Relax | Cozy Ambient Mix'

description = """Welcome to FlyChill. A peaceful 1-hour+ lofi mix — smooth chillhop beats, jazzy piano, mellow bass, and ambient textures. Perfect for studying, working, sleeping, or just unwinding.

🎶 Track List:
1. Window Seat Steam
2. (continued below)

🌙 FlyChill • Lofi • Chill • Chillhop
Perfect for: study, work, sleep, focus, relaxation

🔔 Subscribe for daily lo-fi uploads

© All music produced via Suno AI
"""

tags = ['lofi', 'chillhop', 'chillout', 'chill beats', 'study music', 'sleep music', 'relaxing music', 'ambient', 'jazzy lofi', 'lofi hip hop', 'flychill']

body = {
    'snippet': {
        'title': title,
        'description': description,
        'tags': tags,
        'categoryId': '10',  # Music
        'defaultLanguage': 'en',
    },
    'status': {
        'privacyStatus': 'private',  # private initially, then publish
        'selfDeclaredMadeForKids': False,
        'embeddable': True,
        'publicStatsViewable': True,
    }
}

if publish_at:
    body['status']['publishAt'] = publish_at
    body['status']['privacyStatus'] = 'private'
else:
    body['status']['privacyStatus'] = 'public'

print(f'\nTitle: {title}', file=sys.stderr)
print(f'Description length: {len(description)}', file=sys.stderr)
print(f'Tags: {len(tags)}', file=sys.stderr)
print(f'Video file: {VIDEO_FILE}', file=sys.stderr)
print(f'Publish: {"IMMEDIATE (public)" if not publish_at else f"SCHEDULED at {publish_at} (private until then)"}', file=sys.stderr)

# Check file exists
import os.path
if not os.path.exists(VIDEO_FILE):
    print(f'ERROR: Video file not found: {VIDEO_FILE}', file=sys.stderr)
    sys.exit(1)

file_size = os.path.getsize(VIDEO_FILE)
print(f'File size: {file_size:,} bytes = {file_size / 1024 / 1024:.1f} MB', file=sys.stderr)

# Upload
media = MediaFileUpload(VIDEO_FILE, mimetype='video/mp4', resumable=True, chunksize=1024*1024)

print('\n=== Uploading... ===', file=sys.stderr)
upload_response = youtube.videos().insert(
    part='snippet,status',
    body=body,
    media_body=media,
).execute()

video_id = upload_response['id']
print(f'\n✓ Upload complete!', file=sys.stderr)
print(f'Video ID: {video_id}', file=sys.stderr)
print(f'URL: https://www.youtube.com/watch?v={video_id}', file=sys.stderr)
print(f'Status: {upload_response["status"]["privacyStatus"]}', file=sys.stderr)
if 'publishAt' in upload_response.get('status', {}):
    print(f'Publish at: {upload_response["status"]["publishAt"]}', file=sys.stderr)

# Output as JSON for parsing
result = {
    'video_id': video_id,
    'url': f'https://www.youtube.com/watch?v={video_id}',
    'title': title,
    'channel_id': CHANNEL_ID,
    'channel_handle': '@FlyChill',
    'privacy': upload_response['status']['privacyStatus'],
    'publish_at': upload_response.get('status', {}).get('publishAt'),
    'uploaded_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
print('\n=== JSON OUTPUT ===')
print(json.dumps(result, indent=2))
