#!/usr/bin/env python3
"""
Smart upload: handles YouTube direct API + Zernio for FlyChill.
- No channel name in title
- Multi-language description (English + 5 translations)
- Music category (10)
- No video language (instrumental)
- FlyChill: monetization enabled
"""
import os, sys, json, subprocess, time, random, secrets
import urllib.request, urllib.parse

# Channel configs
def load_nippon_secrets():
    """Load LoFiNippon OAuth secrets from the file"""
    nippon_json_path = '/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json'
    if os.path.exists(nippon_json_path):
        return json.load(open(nippon_json_path))
    # Fall back to env var (if set properly)
    nippon_json = os.environ.get('YOUTUBE_NIPPON_CLIENT_SECRETS_JSON', '')
    if nippon_json.startswith('$(cat'):
        nippon_json = ''
    return json.loads(nippon_json) if nippon_json else {}

CHANNELS = {
    'thelofi': {
        'name': 'TheLoFi',
        'method': 'youtube',
        'channel_id': 'UCpdnbfS3UL-_bKr_8uJGYxQ',
        'refresh_token': os.environ['YOUTUBE_REFRESH_TOKEN'],
        'client_secrets': json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON']),
        'monetize': False,
        'titles': [
            "1 Hour Lofi Beats to Study, Sleep & Relax | Cozy Rain Night Vibes",
            "Late Night Lofi Hip Hop | Cozy Room, Rain Window & Coffee",
            "Chill Lofi Mix | Rain on Glass, Warm Lamp & Reading Vibes",
            "Lofi Hip Hop Radio | Soft Piano, Melancholy Night & Coffee Steam",
            "Rainy Night Lofi | Cozy Study Beats to Focus & Unwind",
            "Slow Lofi Beats | Melancholic Evenings, Vinyl Crackle & Rain",
            "Lofi Sleep Music | Late Night Window Rain & Quiet Room",
            "Cozy Lofi Hip Hop | Warm Lamp, Books & Midnight Rain",
            "Calm Lofi Mix | Late Hours, Tea Steam & Soft Piano",
            "Lofi Chill Beats | Rainy Window, Coffee & Quiet Study Night",
        ],
    },
    'lofinippon': {
        'name': 'LofiNippon',
        'method': 'youtube',
        'channel_id': 'UCEXLQ3tlpMu4TWnHojfEP7g',
        'refresh_token': os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN'],
        'client_secrets': load_nippon_secrets(),
        'monetize': False,
        'titles': [
            "1 Hour Lofi Beats to Study, Sleep & Relax | Japanese Sakura Night",
            "和風ローファイ | 桜の夜、提灯と静かな雨音",
            "Japanese Lofi Hip Hop | Lantern Night, Sakura & Bamboo Rain",
            "和ロフィー | 静寂の茶屋、雨音と竹林の夜",
            "Tokyo Lofi Beats | Tanuki Lanterns, Tatami & Night Rain",
            "禅ローファイ | 桜の夜、提灯と畳の静けさ",
            "Sakura Night Lofi | Japanese Garden, Lanterns & Soft Koto",
            "Lo-Fi Japonés | Flores de Cerezo, Linternas & Lluvia Suave",
            "Lo-Fi Japonais | Jardin Zen, Lanterne & Pluie Douce",
            "Yume Lofi | Japanese Night, Maple Leaves & Tea Ceremony",
        ],
    },
    'flychill': {
        'name': 'FlyChill',
        'method': 'zernio',
        'channel_id': 'UCvnQnOtZUJ9ZsM1ZgJpvBqQ',
        'zernio_account': '6a4076bf9d9472faae0b16dc',
        'monetize': True,
        'titles': [
            "1 Hour Lofi Beats to Study, Sleep & Relax | Rainy Window Night",
            "Chill Lofi Mix | City Rain, Window Lights & Late Night",
            "Lofi Hip Hop Radio | Neon Streets, Rain Drops & Melancholy",
            "Late Night Lofi | Coffee Shop Rain, City Glow & Soft Piano",
            "Urban Lofi Chill | Rainy Window, Bokeh Lights & Quiet Hours",
            "Lofi Sleep Music | City Night, Distant Lights & Soft Beats",
            "Moody Lofi Mix | Window Rain, Lavender Light & Slow Piano",
            "Lofi Hip Hop Beats | City Window, Rain & Midnight Glow",
            "Chillhop Lofi | Neon Rain, Coffee Steam & Late Night Vibes",
            "Quiet Lofi | Cityscape Rain, Warm Light & Reflective Beats",
        ],
    },
}

TAGS = {
    'thelofi': ['lofi', 'lo-fi', 'lofi hip hop', 'chill beats', 'study music', 'sleep music', 'rain sounds', 'cozy room', 'late night', 'relaxing music', 'chillhop', 'lofi mix', '1 hour lofi', 'study beats', 'focus music', 'calm music', 'melancholic', 'piano lofi', 'jazz lofi', 'vinyl crackle'],
    'lofinippon': ['lofi', 'lo-fi', 'japanese lofi', 'study music', 'sleep music', 'sakura', 'lantern', 'tatami', 'zen music', 'chill beats', 'relaxing music', 'bamboo rain', 'japanese aesthetic', 'anime lofi', 'koto', 'tea ceremony', 'meditation', 'calm music'],
    'flychill': ['lofi', 'lo-fi', 'chill beats', 'study music', 'sleep music', 'rain music', 'city lofi', 'urban chill', 'chillhop', 'late night', 'melancholic', 'city lights', 'bokeh', 'relaxing music', 'focus music', '1 hour lofi', 'deep focus', 'coding music', 'rainy window', 'contemplative'],
}

def get_access_token_youtube(cfg):
    cs = cfg['client_secrets']
    data = urllib.parse.urlencode({
        'client_id': cs['installed']['client_id'],
        'client_secret': cs['installed']['client_secret'],
        'refresh_token': cfg['refresh_token'],
        'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request(
        'https://oauth2.googleapis.com/token',
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['access_token']

def upload_youtube_direct(cfg, video_path, title, description, tags, publish_at, monetize=False, thumbnail_path=None):
    token = get_access_token_youtube(cfg)
    
    metadata = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': '10',
            'defaultLanguage': 'en',
            'defaultAudioLanguage': 'en',
        },
        'status': {
            'privacyStatus': 'private',
            'publishAt': publish_at,
            'embeddable': True,
            'license': 'youtube',
            'selfDeclaredMadeForKids': False,
            'madeForKids': False,
            'publicStatsViewable': True,
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
    
    print(f'  Uploading {file_size/1024/1024:.1f}MB...')
    with open(video_path, 'rb') as f:
        upload_req = urllib.request.Request(
            upload_url,
            data=f.read(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'video/mp4',
            },
            method='PUT'
        )
    with urllib.request.urlopen(upload_req, timeout=1800) as r:
        result = json.load(r)
    
    video_id = result['id']
    print(f'  ✓ Uploaded: https://youtube.com/watch?v={video_id}')
    print(f'    Title: {title}')
    print(f'    Publish at: {publish_at}')
    
    # Upload custom thumbnail if provided
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            upload_thumbnail(token, video_id, thumbnail_path)
        except Exception as e:
            print(f'    Thumbnail upload failed: {e}')
    
    return result

def upload_thumbnail(token, video_id, thumbnail_path):
    """Upload custom thumbnail to YouTube"""
    print(f'  Uploading custom thumbnail...')
    with open(thumbnail_path, 'rb') as f:
        thumb_req = urllib.request.Request(
            f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}',
            data=f.read(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'image/png',
            },
            method='POST'
        )
    with urllib.request.urlopen(thumb_req, timeout=60) as r:
        result = json.load(r)
    print(f'    ✓ Thumbnail uploaded')

def upload_zernio(cfg, video_path, title, description, tags, publish_at, monetize=False, thumbnail_path=None):
    api_key = os.environ['ZERNIO_API_KEY']
    file_size = os.path.getsize(video_path)
    
    presign = urllib.request.Request(
        'https://api.zernio.com/api/v1/media/presign',
        data=json.dumps({
            'filename': os.path.basename(video_path),
            'contentType': 'video/mp4',
            'size': file_size,
        }).encode(),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
    )
    with urllib.request.urlopen(presign, timeout=30) as r:
        presign_data = json.load(r)
    upload_url = presign_data['uploadUrl']
    public_url = presign_data['publicUrl']
    
    print(f'  Uploading {file_size/1024/1024:.1f}MB to Zernio...')
    with open(video_path, 'rb') as f:
        put_req = urllib.request.Request(upload_url, data=f.read(), headers={'Content-Type': 'video/mp4'}, method='PUT')
    urllib.request.urlopen(put_req, timeout=1800)
    
    time.sleep(5)
    
    post_body = {
        'title': title,
        'content': description,
        'mediaItems': [{'type': 'video', 'url': public_url}],
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
        'scheduledFor': publish_at,
        'publishNow': False,
    }
    if monetize:
        post_body['platforms'][0]['platformSpecificData']['monetize'] = True
    
    post_req = urllib.request.Request(
        'https://api.zernio.com/api/v1/posts',
        data=json.dumps(post_body).encode(),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
    )
    with urllib.request.urlopen(post_req, timeout=30) as r:
        result = json.load(r)
    
    print(f'  ✓ Zernio post: {result.get("id", "?")}')
    print(f'    Title: {title}')
    print(f'    Publish at: {publish_at}')
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('channel', choices=list(CHANNELS.keys()))
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--publish-at', required=True, help='ISO 8601 datetime (UTC)')
    parser.add_argument('--title', help='Override title')
    parser.add_argument('--thumbnail', help='Path to custom thumbnail')
    args = parser.parse_args()
    
    cfg = CHANNELS[args.channel]
    title = args.title or random.choice(cfg['titles'])
    
    desc_path = f'/workspace/daily-pipeline/desc-{args.channel}-multilang.txt'
    if not os.path.exists(desc_path):
        en_path = f'/workspace/daily-pipeline/desc-{args.channel}-en.txt'
        description = open(en_path).read() if os.path.exists(en_path) else title
    else:
        description = open(desc_path).read()
    
    tags = TAGS[args.channel]
    
    print(f'=== Uploading to {cfg["name"]} ({args.channel}) ===')
    print(f'  Method: {cfg["method"]}')
    print(f'  Monetize: {cfg["monetize"]}')
    print(f'  Title: {title}')
    print(f'  Description: {len(description)} chars (multi-lang)')
    print(f'  Tags: {len(tags)} tags')
    print(f'  Publish: {args.publish_at}')
    print(f'')
    
    if cfg['method'] == 'youtube':
        result = upload_youtube_direct(cfg, args.video, title, description, tags, args.publish_at, cfg['monetize'], args.thumbnail)
    else:
        result = upload_zernio(cfg, args.video, title, description, tags, args.publish_at, cfg['monetize'], args.thumbnail)

if __name__ == '__main__':
    main()
