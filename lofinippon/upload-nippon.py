#!/usr/bin/env python3
"""Upload video to @lofinippon channel.

Uses COMPLETELY SEPARATE credentials from @The-Lo-Fi:
- YOUTUBE_NIPPON_REFRESH_TOKEN
- YOUTUBE_NIPPON_CLIENT_SECRETS_JSON
- YOUTUBE_NIPPON_CHANNEL_ID

NEVER mix up with the @The-Lo-Fi channel (UCpdnbfS3UL-_bKr_8uJGYxQ).
"""
import os, sys, json, datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === LoFi Nippon credentials (NEVER use TheLoFi ones) ===
client_secrets = json.loads(os.environ['YOUTUBE_NIPPON_CLIENT_SECRETS_JSON'])
CLIENT_ID = client_secrets['installed']['client_id']
CLIENT_SECRET = client_secrets['installed']['client_secret']
REFRESH_TOKEN = os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN']
CHANNEL_ID = os.environ['YOUTUBE_NIPPON_CHANNEL_ID']
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']

if REFRESH_TOKEN == 'PENDING_OAUTH_FLOW':
    print('ERROR: YOUTUBE_NIPPON_REFRESH_TOKEN is not yet set.', file=sys.stderr)
    print('Run oauth-nippon.py first to complete the OAuth flow.', file=sys.stderr)
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

# Sanity check - what channel are we uploading to?
print('=== Uploading to @lofinippon ===', file=sys.stderr)
print(f'Channel ID: {CHANNEL_ID}', file=sys.stderr)
print(f'Handle: {os.environ.get("YOUTUBE_NIPPON_CHANNEL_HANDLE", "unknown")}', file=sys.stderr)

VIDEO_FILE = sys.argv[1] if len(sys.argv) > 1 else '/workspace/lofinippon-video-production/lofinippon-final.mp4'

# Schedule publish at 22:00 UTC (= 5 PM EST = 7 AM JST next day)
# For Japanese audience, 23:00-7:00 JST morning is good. JST = UTC+9
# 22:00 UTC = 7 AM JST next day — morning commute time
now = datetime.datetime.now(datetime.timezone.utc)
target_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
if now >= target_time:
    target_time = target_time + datetime.timedelta(days=1)
publish_at = target_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')

jst_time = target_time.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
est_time = target_time.astimezone(datetime.timezone(datetime.timedelta(hours=-5)))

print(f'Current UTC: {now.strftime("%Y-%m-%d %H:%M:%S")}', file=sys.stderr)
print(f'Scheduled publish: {publish_at} UTC', file=sys.stderr)
print(f'  = {est_time.strftime("%Y-%m-%d %H:%M:%S")} EST (US East prime time)', file=sys.stderr)
print(f'  = {jst_time.strftime("%Y-%m-%d %H:%M:%S")} JST (Japan morning)', file=sys.stderr)

# Compose title — Japanese lo-fi aesthetic
title = sys.argv[2] if len(sys.argv) > 2 else '1 Hour+ Japanese Lo-Fi Vibes for Study, Sleep & Focus | Sakura Night, Zen Garden, Tokyo Rain | Lofi Nippon'

description = """Welcome back to LoFi Nippon. A peaceful 1-hour Japanese lo-fi mix — traditional instruments (koto, shamisen, shakuhachi) paired with sakura-pink anime illustrations of Japan.

🎶 Track List:
- Sakura Night Walk
- Tokyo Train Window
- Zen Garden
- Bamboo Forest
- Tea Ceremony
- Torii Gate Path
- Old Kyoto Alley
- Tsukimi Moon
- Sake Bar
- Mount Fuji Dawn

🎨 Original Japanese-themed anime illustrations
🎵 AI-generated lo-fi production (Suno v5.5)
✨ Vibe: Tranquil, Nostalgic, Zen, Cinematic Japan

Best listened to for:
- Late night studying 📚
- Falling asleep 💤
- Meditation & focus 🧘
- Working in a cozy space ☕

If you enjoy the vibe, please like and subscribe. ありがとうございます。

#lofi #japaneselofi #koto #shakuhachi #zen #sakura #study #sleep #japan #lofinippon"""

tags = ['lofi', 'japanese lofi', 'japan', 'koto', 'shakuhachi', 'shamisen', 'zen', 'sakura', 'tokyo', 'study music', 'sleep music', 'instrumental', 'lofinippon', 'anime']

body = {
    'snippet': {
        'title': title,
        'description': description,
        'tags': tags,
        'categoryId': '10',
        'defaultLanguage': 'en',
    },
    'status': {
        'privacyStatus': 'private',
        'publishAt': publish_at,
        'selfDeclaredMadeForKids': False,
    },
}

print(f'\nUploading: {VIDEO_FILE}', file=sys.stderr)
print(f'Size: {os.path.getsize(VIDEO_FILE) / 1024 / 1024:.1f} MB', file=sys.stderr)

media = MediaFileUpload(VIDEO_FILE, mimetype='video/mp4', resumable=True, chunksize=1024*1024*10)
request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

response = None
last_pct = -1
while response is None:
    status, response = request.next_chunk()
    if status:
        pct = int(status.progress() * 100)
        if pct != last_pct and pct % 10 == 0:
            print(f'  Progress: {pct}%', file=sys.stderr)
            last_pct = pct

print(file=sys.stderr)
print(f'✓ Upload complete to @lofinippon!', file=sys.stderr)
print(f'  Video ID: {response["id"]}', file=sys.stderr)
print(f'  URL: https://www.youtube.com/watch?v={response["id"]}', file=sys.stderr)
print(f'  Publish at: {publish_at}', file=sys.stderr)

with open('/workspace/lofinippon-pipeline/last-upload.json', 'w') as f:
    json.dump({
        'channel': '@lofinippon',
        'channel_id': CHANNEL_ID,
        'id': response['id'],
        'title': title,
        'url': f'https://www.youtube.com/watch?v={response["id"]}',
        'publishAt': publish_at,
    }, f, indent=2)

print(file=sys.stderr)
print(json.dumps({
    'id': response['id'],
    'url': f'https://www.youtube.com/watch?v={response["id"]}',
    'publishAt': publish_at,
}))