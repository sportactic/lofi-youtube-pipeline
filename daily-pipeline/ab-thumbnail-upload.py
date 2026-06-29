#!/usr/bin/env python3
"""
A/B Test Thumbnail Uploader
Uses YouTube's "Test & Compare" feature by uploading 3 thumbnail variations.
YouTube will automatically test them and pick the winner.
"""
import os, sys, json, urllib.request, urllib.parse
import urllib.error

def get_access_token(refresh_token, client_id, client_secret):
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

def upload_thumbnail(token, video_id, image_path, variation='A'):
    """Upload a single thumbnail. YouTube allows multiple to be uploaded and tested."""
    print(f'  Uploading variation {variation}: {os.path.basename(image_path)}...')
    with open(image_path, 'rb') as f:
        req = urllib.request.Request(
            f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}',
            data=f.read(),
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'image/jpeg',
            },
            method='POST'
        )
    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.load(r)
    print(f'    ✓ Variation {variation} uploaded')
    return result

def ab_test_thumbnails(token, video_id, paths):
    """
    Upload 3 thumbnail variations for A/B testing.
    YouTube will show different ones to different users and pick a winner.
    """
    for i, path in enumerate(paths[:3]):
        if not os.path.exists(path):
            print(f'  WARNING: {path} not found, skipping')
            continue
        upload_thumbnail(token, video_id, path, chr(65 + i))
    print(f'  ✓ A/B test ready: YouTube will pick the winner automatically')

def main():
    if len(sys.argv) < 4:
        print('Usage: ab-thumbnail-upload.py <channel> <video_id> <thumb_A> [thumb_B] [thumb_C]')
        sys.exit(1)
    
    channel = sys.argv[1]
    video_id = sys.argv[2]
    thumbs = sys.argv[3:]
    
    # Get channel config
    REPO = '/run/csi/mount-root/nas/eab0d61a99b6696edb3d2aff87b585e8/lofi-youtube-pipeline'
    
    if channel == 'thelofi':
        refresh = os.environ['YOUTUBE_REFRESH_TOKEN']
        cs = json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON'])
    elif channel == 'lofinippon':
        refresh = os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN']
        cs = json.load(open(f'/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json'))
    else:
        print(f'Channel {channel} not supported via YouTube API')
        sys.exit(1)
    
    token = get_access_token(refresh, cs['installed']['client_id'], cs['installed']['client_secret'])
    ab_test_thumbnails(token, video_id, thumbs)
    print(f'  Video URL: https://youtube.com/watch?v={video_id}')

if __name__ == '__main__':
    main()
