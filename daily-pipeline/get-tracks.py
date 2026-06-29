#!/usr/bin/env python3
"""Fetch track manifest from Suno workspaces - one per channel"""
import os, sys, json
import urllib.request

JWT_PATH = '/workspace/suno-jwt.txt'
WORKSPACES = {
    'thelofi': '78136c59-6637-4eea-beba-9582e58b028d',
    'lofinippon': '2f6a96be-2327-4b87-baec-d21466d6d3c5',
    'flychill': '7b661a9c-107a-4297-b0ee-2fa015e66d8b',
}
VISUALS = {
    'thelofi': '/workspace/visuals-thelofi-v3',
    'lofinippon': '/workspace/visuals-lofi-nippon-v3',
    'flychill': '/workspace/visuals-fly-chill-v3',
}

def fetch(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def main():
    channel = sys.argv[1] if len(sys.argv) > 1 else 'thelofi'
    if channel not in WORKSPACES:
        print(f'Unknown channel: {channel}. Use: {list(WORKSPACES.keys())}')
        sys.exit(1)
    
    JWT = open(JWT_PATH).read().strip()
    ws_id = WORKSPACES[channel]
    
    headers = {
        'Authorization': f'Bearer {JWT}',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Origin': 'https://suno.com',
        'Referer': 'https://suno.com/',
        'Accept': 'application/json, text/plain, */*',
    }
    
    data = fetch(f'https://studio-api-prod.suno.com/api/project/{ws_id}', headers)
    
    clips = data.get('project_clips', [])
    v55 = [c['clip'] for c in clips if c['clip'].get('major_model_version') == 'v5.5']
    
    manifest = {
        'channel': channel,
        'workspace_id': ws_id,
        'tracks': [],
        'visuals_dir': VISUALS[channel],
    }
    for c in v55:
        manifest['tracks'].append({
            'id': c['id'],
            'title': c['title'],
            'duration': c['metadata']['duration'],
            'audio_url': c['audio_url'],
            'image_url': c.get('image_url'),
            'created_at': c['created_at'],
            'gpt_description_prompt': c['metadata'].get('gpt_description_prompt', ''),
        })
    
    manifest_path = f'/workspace/daily-pipeline/manifest-{channel}.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f'{channel}: {len(v55)} v5.5 tracks')
    print(f'  Total duration: {sum(t["duration"] for t in manifest["tracks"]):.0f}s = {sum(t["duration"] for t in manifest["tracks"])/60:.1f} min')
    print(f'  Saved to: {manifest_path}')
    print(f'  Visuals: {VISUALS[channel]}')

if __name__ == '__main__':
    main()
