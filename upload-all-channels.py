#!/usr/bin/env python3
"""Upload all 3 channels with staggered schedule."""
import json, os, subprocess, sys, time
import urllib.request, urllib.parse

with open('/workspace/all-channels-pipeline/suno-workspaces.json') as f:
    WS = json.load(f)

# Load Nippon secrets from file (env var is shell-substituted incorrectly)
with open('/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json') as f:
    NIPPON_SECRETS = json.load(f)

CHANNELS = {
    'thelofi': {
        'youtube_id': WS['workspaces']['the-lofi']['youtube_channel_id'],
        'method': 'youtube',
        'refresh_token': os.environ['YOUTUBE_REFRESH_TOKEN'],
        'client_secrets': json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON']),
        'video_file': '/workspace/v3-thelofi-prod/final.mp4',
        'title': 'The Lo-Fi • 85 Min+ Cozy Lofi Beats to Study Sleep Relax | Rainy Window Vibes',
        'tags': ['lofi', 'chillhop', 'chillout', 'cozy', 'rainy', 'study music', 'anime',
                 'chill beats', 'the lo fi', 'lofi hip hop', '90s anime', 'lofi vibes'],
    },
    'lofinippon': {
        'youtube_id': WS['workspaces']['lofinippon']['youtube_channel_id'],
        'method': 'youtube',
        'refresh_token': os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN'],
        'client_secrets': NIPPON_SECRETS,
        'video_file': '/workspace/v3-lofi-nippon-prod/final.mp4',
        'title': 'Lofi Nippon • 75 Min+ Japanese Lo-Fi Beats to Study Sleep Relax | Lantern & Tanuki Vibes',
        'tags': ['lofi', 'japanese lofi', 'chillhop', 'chillout', 'japan', 'kimono', 'tanuki',
                 'traditional', 'koto', 'shakuhachi', 'lofi hip hop', 'anime', 'studio ghibli',
                 'sakura', 'study music', 'relaxing'],
    },
    'flychill': {
        'method': 'zernio',
        'account_id': '6a4076bf9d9472faae0b16dc',
        'api_key': 'sk_a959595f37d9067a4e21206d94efb8a77894ad0dc4bf82967e65785f62843822',
        'youtube_id': WS['workspaces']['flychill']['youtube_channel_id'],
        'video_file': '/workspace/v3-fly-chill-prod/final.mp4',
        'title': 'FlyChill • 75 Min+ Lofi Beats to Study Sleep Relax | Anime Café Vibes',
        'tags': ['lofi', 'chillhop', 'chillout', 'ambient lofi', 'cafe vibes', 'anime',
                 'espresso', 'study music', 'relaxing music', 'lofi hip hop', 'flychill'],
    },
}

SCHED = {
    'thelofi': '2026-06-29T19:00:00Z',     # TR 22:00 today
    'lofinippon': '2026-06-30T01:00:00Z',  # TR 04:00 tomorrow
    'flychill': '2026-06-30T07:00:00Z',    # TR 10:00 tomorrow
}


def get_access_token(refresh_token, secrets):
    cid = secrets['installed']['client_id']
    cs = secrets['installed']['client_secret']
    data = urllib.parse.urlencode({
        'client_id': cid,
        'client_secret': cs,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, method='POST')
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return resp['access_token']


def upload_youtube(name, cfg):
    print(f"\n{'='*60}\n=== {name.upper()} (YouTube Direct) ===\n{'='*60}")
    access_token = get_access_token(cfg['refresh_token'], cfg['client_secrets'])
    print(f"  ✓ Got access token")
    
    video_file = cfg['video_file']
    size = os.path.getsize(video_file)
    scheduled = SCHED[name]
    
    print(f"  Video: {video_file} ({size//1024//1024}MB)")
    print(f"  Schedule: {scheduled}")
    
    # Descriptions
    if name == 'thelofi':
        desc = ("🎵 The Lo-Fi 85+ minutes of pure cozy lofi bliss — 20 fresh tracks cycling through 20 anime-girl-and-chameleon scenes of rainy windows, lamp-lit reading nooks, rooftop study skies, and quiet midnight walks. Perfect for studying, coding, sleeping, or unwinding.\n\n"
                "🌙 The Lo-Fi • Lofi • Chill • Chillhop • Cozy Anime Aesthetic\n"
                "Perfect for: study, work, sleep, focus, relaxation\n\n"
                "🔔 Subscribe for daily lo-fi uploads!\n\n"
                "#lofi #chillhop #chillout #cozy #rainywindow #anime #studymusic #sleepmusic #relaxingmusic")
    elif name == 'lofinippon':
        desc = ("🎵 Lofi Nippon 75+ minutes of Japanese traditional lo-fi bliss — 10 fresh tracks cycling through 10 kimono-girl-and-tanuki scenes of lantern alleys, tea ceremonies, bamboo rain, and matsuri festivals. Perfect for studying, coding, sleeping, or unwinding.\n\n"
                "🌙 Lofi Nippon • Japanese Lo-Fi • Traditional Meets Modern\n"
                "Perfect for: study, work, sleep, focus, relaxation\n\n"
                "🔔 Subscribe for daily lo-fi uploads!\n\n"
                "#lofi #japaneselofi #chillhop #chillout #japan #kimono #tanuki #sakura #studymusic")
    
    init_url = 'https://www.googleapis.com/upload/youtube/v3/videos?part=snippet,status&uploadType=resumable'
    body = {
        'snippet': {
            'title': cfg['title'],
            'description': desc,
            'tags': cfg['tags'],
            'categoryId': '10',
        },
        'status': {
            'privacyStatus': 'private',  # Must be private for publishAt to work
            'publishAt': scheduled,
            'embeddable': True,
            'license': 'youtube',
            'selfDeclaredMadeForKids': False,
        }
    }
    
    print(f"  Step 1: Initiate resumable upload...")
    init_req = urllib.request.Request(
        init_url,
        data=json.dumps(body).encode(),
        method='POST',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Upload-Content-Type': 'video/mp4',
            'X-Upload-Content-Length': str(size),
        }
    )
    init_resp = urllib.request.urlopen(init_req, timeout=60)
    upload_url = init_resp.headers.get('Location') or init_resp.headers.get('location')
    if not upload_url:
        print(f"  ✗ No upload URL")
        print(init_resp.read()[:500])
        return None
    
    print(f"  ✓ Upload URL acquired")
    
    print(f"  Step 2: PUT {size//1024//1024}MB...")
    with open(video_file, 'rb') as f:
        put_req = urllib.request.Request(upload_url, data=f.read(), method='PUT',
                                          headers={'Content-Type': 'video/mp4'})
        put_resp = urllib.request.urlopen(put_req, timeout=1800)
        result = json.loads(put_resp.read())
    
    video_id = result.get('id')
    print(f"  ✓ YouTube video ID: {video_id}")
    print(f"  Privacy: {result.get('status', {}).get('privacyStatus', '?')}")
    print(f"  publishAt: {result.get('status', {}).get('publishAt', '?')}")
    return video_id


def upload_zernio(name, cfg):
    print(f"\n{'='*60}\n=== {name.upper()} (Zernio) ===\n{'='*60}")
    api_key = cfg['api_key']
    account_id = cfg['account_id']
    video_file = cfg['video_file']
    size = os.path.getsize(video_file)
    scheduled = SCHED[name]
    
    print(f"  Video: {video_file} ({size//1024//1024}MB)")
    print(f"  Schedule: {scheduled}")
    
    def req(method, path, data=None):
        url = f"https://zernio.com{path}"
        headers = {"Authorization": f"Bearer {api_key}"}
        body = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data).encode()
        r = urllib.request.Request(url, data=body, method=method, headers=headers)
        return json.loads(urllib.request.urlopen(r, timeout=900).read())
    
    print(f"  Step 1: Presign...")
    presign = req("POST", "/api/v1/media/presign", {
        "filename": os.path.basename(video_file),
        "contentType": "video/mp4",
        "size": size
    })
    public_url = presign['publicUrl']
    print(f"  ✓ Presigned")
    
    print(f"  Step 2: PUT to R2...")
    with open(video_file, 'rb') as f:
        put_req = urllib.request.Request(presign['uploadUrl'], data=f.read(), method='PUT',
                                          headers={"Content-Type": "video/mp4"})
        urllib.request.urlopen(put_req, timeout=1800)
    print(f"  ✓ Uploaded to R2")
    
    time.sleep(5)
    
    print(f"  Step 3: Create scheduled post...")
    desc = ("🎵 FlyChill 75+ minutes of pure lofi bliss — 10 fresh tracks cycling through 10 anime-girl scenes of cozy cafes, skylight rain, paper cup reflections, and quiet corner tables. Perfect for studying, coding, sleeping, or unwinding.\n\n"
            "🌙 FlyChill • Lofi • Chill • Chillhop • Anime Aesthetic\n"
            "Perfect for: study, work, sleep, focus, relaxation\n\n"
            "🔔 Subscribe for daily lo-fi uploads!\n\n"
            "#lofi #chillhop #chillout #ambient #cafevibes #anime #espresso #studymusic #sleepmusic #flychill")
    
    post = req("POST", "/api/v1/posts", {
        "content": desc,
        "title": cfg['title'],
        "mediaItems": [{"type": "video", "url": public_url}],
        "platforms": [{
            "platform": "youtube",
            "accountId": account_id,
            "platformSpecificData": {
                "title": cfg['title'],
                "description": desc,
                "visibility": "public",
                "tags": cfg['tags'],
            }
        }],
        "scheduledFor": scheduled,
        "publishNow": False
    })
    
    post_id = post.get('post', post).get('_id')
    print(f"  ✓ Zernio post ID: {post_id}")
    print(f"  ✓ Scheduled for: {scheduled}")
    return post_id


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if target == 'all':
        for name, cfg in CHANNELS.items():
            try:
                if cfg['method'] == 'youtube':
                    upload_youtube(name, cfg)
                else:
                    upload_zernio(name, cfg)
            except Exception as e:
                print(f"  ✗ {name} failed: {e}")
                import traceback
                traceback.print_exc()
    else:
        cfg = CHANNELS[target]
        if cfg['method'] == 'youtube':
            upload_youtube(target, cfg)
        else:
            upload_zernio(target, cfg)
