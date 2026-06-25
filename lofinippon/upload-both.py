#!/usr/bin/env python3
"""Upload both LoFi Nippon videos with different scheduled publish times."""
import os, sys, json, datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# LoFi Nippon credentials - load from local token file (set by oauth-interactive.py)
with open(os.path.join(os.path.dirname(__file__), 'token-nippon.json')) as f:
    token_data = json.load(f)
CLIENT_ID = token_data['client_id']
CLIENT_SECRET = token_data['client_secret']
REFRESH_TOKEN = token_data['refresh_token']
CHANNEL_ID = os.environ.get('YOUTUBE_NIPPON_CHANNEL_ID', 'UCEXLQ3tlpMu4TWnHojfEP7g')
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl', 'https://www.googleapis.com/auth/youtube']

creds = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    token_uri='https://oauth2.googleapis.com/token',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=SCOPES,
)
youtube = build('youtube', 'v3', credentials=creds)

# Different publish times — V1 tomorrow morning JST, V2 day after evening
now = datetime.datetime.now(datetime.timezone.utc)

# V1: tomorrow 22:00 UTC = JST 7 AM next day (Japan morning commute)
v1_target = now.replace(hour=22, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
# V2: 2 days later 12:00 UTC = JST 9 PM (Japan evening)
v2_target = now.replace(hour=12, minute=0, second=0, microsecond=0) + datetime.timedelta(days=2)

v1_publish = v1_target.strftime('%Y-%m-%dT%H:%M:%S.000Z')
v2_publish = v2_target.strftime('%Y-%m-%dT%H:%M:%S.000Z')

def upload(video_path, title, description, tags, publish_at, label):
    print(f'\n=== Uploading {label} ===', file=sys.stderr)
    print(f'  Video: {video_path}', file=sys.stderr)
    print(f'  Size: {os.path.getsize(video_path)/1024/1024:.1f} MB', file=sys.stderr)
    print(f'  Publish: {publish_at} UTC', file=sys.stderr)
    jst = datetime.datetime.strptime(publish_at, '%Y-%m-%dT%H:%M:%S.000Z').replace(tzinfo=datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=9)))
    est = datetime.datetime.strptime(publish_at, '%Y-%m-%dT%H:%M:%S.000Z').replace(tzinfo=datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=-5)))
    print(f'  = {jst.strftime("%Y-%m-%d %H:%M JST")}', file=sys.stderr)
    print(f'  = {est.strftime("%Y-%m-%d %H:%M EST")}', file=sys.stderr)

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
    media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True, chunksize=1024*1024*10)
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
    print(f'  ✓ Uploaded: {response["id"]}', file=sys.stderr)
    return response['id']

# V1 description
v1_desc = """Welcome to LoFi Nippon. A peaceful 1 hour+ Japanese lo-fi mix.

🎶 Track List (Variation A):
- Fuji Morning
- Yoru no Izakaya
- Moon Garden Drift
- Lanterns in Kyoto
- Fog at Torii Path
- Tea Room Ripples
- Bamboo Moon Drift
- Bamboo Water Path
- Shibuya Raincar
- Sakura Bell Drift

🎨 Original kimono + tanuki anime illustrations
🎵 AI-generated v5.5 lo-fi (Suno chirp-fenix)
✨ Vibe: Tranquil, Nostalgic, Zen, Cinematic Japan

Best for: late night studying, falling asleep, meditation, working in a cozy space.

If you enjoy, please like and subscribe. ありがとうございます。

#lofi #japaneselofi #koto #shakuhachi #shamisen #zen #sakura #tokyo #study #sleep #japan #lofinippon"""

v2_desc = """Welcome to LoFi Nippon. Another peaceful 1 hour+ Japanese lo-fi mix.

🎶 Track List (Variation B — alternate takes):
- Fuji Morning (alt)
- Yoru no Izakaya (alt)
- Moon Garden Drift (alt)
- Lanterns in Kyoto (alt)
- Fog at Torii Path (alt)
- Tea Room Ripples (alt)
- Bamboo Moon Drift (alt)
- Bamboo Water Path (alt)
- Shibuya Raincar (alt)
- Sakura Bell Drift (alt)

🎨 Original kimono + tanuki anime illustrations
🎵 AI-generated v5.5 lo-fi (Suno chirp-fenix)
✨ Vibe: Tranquil, Nostalgic, Zen, Cinematic Japan

Best for: late night studying, falling asleep, meditation, working in a cozy space.

If you enjoy, please like and subscribe. ありがとうございます。

#lofi #japaneselofi #koto #shakuhachi #shamisen #zen #sakura #tokyo #study #sleep #japan #lofinippon"""

tags = ['lofi', 'japanese lofi', 'japan', 'koto', 'shakuhachi', 'shamisen', 'zen', 'sakura', 'tokyo', 'study music', 'sleep music', 'instrumental', 'lofinippon', 'anime', 'japan lofi', 'kimono']

# Upload V1
v1_id = upload(
    '/workspace/lofinippon-video-production/lofinippon-v1-final.mp4',
    '1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, Zen Garden, Tokyo Rain | Lofi Nippon v1',
    v1_desc, tags, v1_publish, 'V1',
)

# Upload V2
v2_id = upload(
    '/workspace/lofinippon-video-production/lofinippon-v2-final.mp4',
    '1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, Zen Garden, Tokyo Rain | Lofi Nippon v2',
    v2_desc, tags, v2_publish, 'V2',
)

result = {
    'v1': {
        'id': v1_id,
        'url': f'https://www.youtube.com/watch?v={v1_id}',
        'publishAt': v1_publish,
    },
    'v2': {
        'id': v2_id,
        'url': f'https://www.youtube.com/watch?v={v2_id}',
        'publishAt': v2_publish,
    },
}
print(json.dumps(result, indent=2))
with open('/workspace/lofinippon-pipeline/last-uploads.json', 'w') as f:
    json.dump(result, f, indent=2)