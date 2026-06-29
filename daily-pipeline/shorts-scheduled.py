#!/usr/bin/env python3
"""
Upload 1 Short per channel, scheduled for the NEXT 6-hour slot.
Ensures shorts are spaced 6 hours apart instead of all at once.
"""
import os, sys, json, urllib.request, urllib.parse
import urllib.error
import random
from datetime import datetime, timedelta, timezone

def get_access_token_youtube(refresh_token, client_id, client_secret):
    data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['access_token']

def get_next_6h_slot_utc(channel_offset):
    """Get next 6-hour slot for this channel (offset by channel_offset hours from 0/6/12/18)"""
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    
    # Base slots: 0, 6, 12, 18
    base_slots = [0, 6, 12, 18]
    # Channel offset shifts slots
    channel_slots = [(s + channel_offset) % 24 for s in base_slots]
    
    # Find next slot > current_hour
    for slot in sorted(channel_slots):
        if slot > current_hour:
            target = now.replace(hour=slot, minute=0, second=0, microsecond=0)
            return target
    # Otherwise next day's first slot
    target = (now + timedelta(days=1)).replace(hour=sorted(channel_slots)[0], minute=0, second=0, microsecond=0)
    return target

SHORT_TITLES = {
    'thelofi': [
        "Cozy Rain Lofi 🌧️ | 1 Min Study Break #Shorts",
        "Late Night Lofi 🌙 | Cozy Room Vibes #Shorts",
        "Chill Beats in 60s 🎧 | Window Rain #Shorts",
        "Soft Lofi Piano ☕ | Coffee & Books #Shorts",
        "Lofi for Focus 📚 | 1 Min Melody #Shorts",
        "Rainy Day Lofi 🌧️ | Cozy Moment #Shorts",
        "Melancholic Lofi 🌃 | Vinyl Crackle #Shorts",
        "Study Lofi in 60s 📖 | Late Night #Shorts",
    ],
    'lofinippon': [
        "Japanese Lofi in 60s 🌸 | Sakura Night #Shorts",
        "和風ローファイ 🌙 | 1分間の静けさ #Shorts",
        "Tanuki & Lanterns 🏮 | Lofi Moment #Shorts",
        "禅ローファイ 🍵 | 1 Min Zen #Shorts",
        "Bamboo Rain Lofi 🎋 | Japanese Vibes #Shorts",
        "Tea Ceremony Lofi 🍵 | Soft Moment #Shorts",
        "Japanese Lofi 1分 ⛩️ | Sakura & Night #Shorts",
    ],
    'flychill': [
        "City Rain Lofi 🌃 | 1 Min Escape #Shorts",
        "Late Night Lofi 🌧️ | Window Glow #Shorts",
        "Urban Lofi 60s 🌆 | Coffee Steam #Shorts",
        "Rainy Window Lofi 💭 | Late Hours #Shorts",
        "Chill Lofi Moment 🎧 | City Lights #Shorts",
        "Neon Lofi Vibes 🌃 | 1 Min Study #Shorts",
    ],
}

SHORT_DESCRIPTIONS = {
    'thelofi': """🎧 1 minute of cozy lofi beats

Rain ambience + soft piano + warm lamp light. The perfect study break.

🎵 Full 1 hour mix → check our channel
#Lofi #ChillBeats #StudyMusic #Shorts""",
    'lofinippon': """🌸 1 minute of Japanese lofi

Lantern night + sakura petals + tanuki. A moment of zen.

🎵 Full mix → check our channel
#Lofi #JapaneseLofi #Sakura #Shorts""",
    'flychill': """🌃 1 minute of urban chill lofi

City rain + window lights + soft piano. Late night vibes.

🎵 Full mix → check our channel
#Lofi #ChillBeats #CityLofi #Shorts""",
}

SHORT_TAGS = {
    'thelofi': ['shorts', 'lofi', 'study music', 'chill beats', 'rain sounds', 'cozy', '1 minute lofi'],
    'lofinippon': ['shorts', 'lofi', 'japanese lofi', 'sakura', 'tanuki', 'zen', 'chill'],
    'flychill': ['shorts', 'lofi', 'chill beats', 'city lofi', 'rain music', 'urban chill', '1 minute lofi'],
}

def upload_scheduled_short_youtube(cfg, video_path, channel, publish_at, thumbnail_path=None):
    """Upload a Short with scheduled publish time (6 hours from now)"""
    token = get_access_token_youtube(cfg['refresh_token'], cfg['client_id'], cfg['client_secret'])
    
    title = random.choice(SHORT_TITLES[channel])
    description = SHORT_DESCRIPTIONS[channel]
    tags = SHORT_TAGS[channel]
    
    metadata = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '10',
            'defaultLanguage': 'en',
        },
        'status': {
            'privacyStatus': 'private',
            'publishAt': publish_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'selfDeclaredMadeForKids': False,
            'madeForKids': False,
            'embeddable': True,
        }
    }
    
    file_size = os.path.getsize(video_path)
    init_req = urllib.request.Request(
        f'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        data=json.dumps(metadata).encode(),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Upload-Content-Type': 'video/mp4',
            'X-Upload-Content-Length': str(file_size),
        },
        method='POST'
    )
    with urllib.request.urlopen(init_req, timeout=30) as r:
        upload_url = r.headers.get('Location')
    
    print(f'  Uploading {file_size/1024/1024:.1f}MB → scheduled for {publish_at.strftime("%Y-%m-%d %H:%M UTC")}')
    with open(video_path, 'rb') as f:
        upload_req = urllib.request.Request(
            upload_url,
            data=f.read(),
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'video/mp4'},
            method='PUT'
        )
    with urllib.request.urlopen(upload_req, timeout=600) as r:
        result = json.load(r)
    
    print(f'  ✓ Scheduled: https://youtube.com/shorts/{result["id"]}')
    return result

def upload_scheduled_short_zernio(cfg, video_path, channel, publish_at):
    """Upload via Zernio with scheduled time"""
    api_key = os.environ['ZERNIO_API_KEY']
    file_size = os.path.getsize(video_path)
    
    presign = urllib.request.Request(
        'https://api.zernio.com/api/v1/media/presign',
        data=json.dumps({
            'filename': os.path.basename(video_path),
            'contentType': 'video/mp4',
            'size': file_size,
        }).encode(),
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(presign, timeout=30) as r:
        presign_data = json.load(r)
    
    print(f'  Uploading {file_size/1024/1024:.1f}MB to Zernio...')
    with open(video_path, 'rb') as f:
        req = urllib.request.Request(
            presign_data['uploadUrl'],
            data=f.read(),
            headers={'Content-Type': 'video/mp4'},
            method='PUT'
        )
    urllib.request.urlopen(req, timeout=600)
    
    import time
    time.sleep(3)
    
    title = random.choice(SHORT_TITLES[channel])
    description = SHORT_DESCRIPTIONS[channel]
    tags = SHORT_TAGS[channel]
    
    post = {
        'title': title,
        'content': description,
        'mediaItems': [{'type': 'video', 'url': presign_data['publicUrl'], 'isShort': True}],
        'platforms': [{
            'platform': 'youtube',
            'accountId': cfg['zernio_account'],
            'platformSpecificData': {
                'title': title,
                'description': description,
                'visibility': 'public',
                'tags': tags,
                'categoryId': '10',
                'madeForKids': False,
            }
        }],
        'scheduledFor': publish_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'publishNow': False,
    }
    
    req = urllib.request.Request(
        'https://api.zernio.com/api/v1/posts',
        data=json.dumps(post).encode(),
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.load(r)
    print(f'  ✓ Zernio scheduled: {result.get("id", "?")}')
    return result

# Channel offset for 6-hour slot assignment
CHANNEL_OFFSETS = {
    'thelofi': 0,      # slots: 0, 6, 12, 18
    'lofinippon': 1,   # slots: 1, 7, 13, 19
    'flychill': 2,     # slots: 2, 8, 14, 20
}

def main():
    if len(sys.argv) < 3:
        print('Usage: shorts-scheduled.py <channel> <video_path>')
        sys.exit(1)
    
    channel = sys.argv[1]
    video_path = sys.argv[2]
    
    if not os.path.exists(video_path):
        print(f'Video not found: {video_path}')
        sys.exit(1)
    
    offset = CHANNEL_OFFSETS[channel]
    publish_at = get_next_6h_slot_utc(offset)
    
    print(f'=== Scheduled Short Upload ===')
    print(f'  Channel: {channel}')
    print(f'  Video: {video_path}')
    print(f'  Publish at: {publish_at.strftime("%Y-%m-%d %H:%M UTC")} ({publish_at.strftime("%a %H:%M")})')
    
    if channel == 'thelofi':
        cs = json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON'])
        cfg = {
            'refresh_token': os.environ['YOUTUBE_REFRESH_TOKEN'],
            'client_id': cs['installed']['client_id'],
            'client_secret': cs['installed']['client_secret'],
        }
        upload_scheduled_short_youtube(cfg, video_path, channel, publish_at)
    elif channel == 'lofinippon':
        cs = json.load(open('/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json'))
        cfg = {
            'refresh_token': os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN'],
            'client_id': cs['installed']['client_id'],
            'client_secret': cs['installed']['client_secret'],
        }
        upload_scheduled_short_youtube(cfg, video_path, channel, publish_at)
    elif channel == 'flychill':
        cfg = {'zernio_account': '6a4076bf9d9472faae0b16dc'}
        upload_scheduled_short_zernio(cfg, video_path, channel, publish_at)

if __name__ == '__main__':
    main()
