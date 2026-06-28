#!/usr/bin/env python3
"""Download FlyChill tracks from Suno share URLs via CDN + /api/clip/ endpoint.

Usage:
  python3 download-flychill-tracks.py URL [URL ...]

For each share URL like https://suno.com/s/Wu2jirQenb9zck5O:
1. Fetch the share page → extract clip_id (UUID)
2. Query /api/clip/{clip_id} for full metadata
3. Download https://cdn1.suno.ai/{clip_id}.mp3

Outputs:
  /workspace/flychill-tracks/{NN}-{safe_title}-{clip_short}.mp3
  /workspace/flychill-tracks/manifest.json (with all metadata)
"""
import sys, re, json, time, urllib.request, urllib.parse, os
from pathlib import Path

OUTPUT_DIR = Path("/workspace/flychill-tracks")
OUTPUT_DIR.mkdir(exist_ok=True)

# Read JWT from env or file
JWT = os.environ.get('SUNO_JWT')
if not JWT:
    bearer_file = Path("/workspace/suno-bearer.txt")
    if bearer_file.exists():
        JWT = bearer_file.read_text().strip()
        if JWT.startswith("Bearer "):
            JWT = JWT[7:]

UUID_RE = re.compile(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}')


def get_clip_info_from_share(url):
    """Fetch share URL, extract UUID and basic info from HTML."""
    print(f"  → fetching share page: {url}")
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode('utf-8', errors='replace')
    
    # Extract UUID from audio_url or image_url
    audio_match = re.search(r'cdn\d?\.suno\.ai/([a-f0-9-]{36})\.mp3', html)
    image_match = re.search(r'cdn\d?\.suno\.ai/image_(?:large_)?([a-f0-9-]{36})\.jpeg', html)
    if audio_match:
        clip_id = audio_match.group(1)
    elif image_match:
        clip_id = image_match.group(1)
    else:
        uuids = UUID_RE.findall(html)
        if not uuids:
            raise RuntimeError(f"No UUID found in {url}")
        clip_id = uuids[0]
    
    # Find title (og:title)
    title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    title = title_match.group(1) if title_match else clip_id[:8]
    title = title.replace(' | Suno', '').strip()
    
    return clip_id, title


def get_clip_metadata(clip_id):
    """Query /api/clip/{id} for full metadata."""
    if not JWT:
        return None
    url = f"https://studio-api-prod.suno.com/api/clip/{clip_id}"
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {JWT}',
        'Origin': 'https://suno.com',
        'Referer': 'https://suno.com/me',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        # 403 might be due to missing headers from urllib - retry with curl
        print(f"  ⚠ urllib got {e.code}, retrying with curl...")
        try:
            import subprocess
            result = subprocess.run([
                'curl', '-s',
                '-H', f'Authorization: Bearer {JWT}',
                '-H', 'Origin: https://suno.com',
                '-H', 'Referer: https://suno.com/me',
                '-H', 'Accept: application/json',
                url
            ], capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
        except Exception as e2:
            print(f"  ⚠ curl retry failed: {e2}")
        return None
    except Exception as e:
        print(f"  ⚠ metadata fetch failed: {e}")
        return None


def safe_filename(name):
    return re.sub(r'[^a-zA-Z0-9_-]+', '-', name).strip('-').lower()[:50]


def main(urls):
    if not urls:
        print("Usage: python3 download-flychill-tracks.py URL [URL ...]")
        print("Example: python3 download-flychill-tracks.py https://suno.com/s/Wu2jirQenb9zck5O")
        sys.exit(1)
    
    results = []
    for idx, url in enumerate(urls, 1):
        print(f"\n[{idx}/{len(urls)}] Processing {url}")
        try:
            clip_id, title = get_clip_info_from_share(url)
            print(f"  ✓ clip_id: {clip_id}")
            print(f"  ✓ title (from HTML): {title}")
            
            # Get full metadata from /api/clip/{id}
            metadata = get_clip_metadata(clip_id)
            if metadata:
                title = metadata.get('title', title)
                model = metadata.get('major_model_version', '?')
                duration = metadata.get('metadata', {}).get('duration', 0)
                prompt = metadata.get('metadata', {}).get('gpt_description_prompt', '')
                print(f"  ✓ title (from API): {title}")
                print(f"  ✓ model: v{model}, duration: {duration:.1f}s")
                print(f"  ✓ prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
            else:
                model = '?'
                duration = 0
                prompt = ''
            
            # Download MP3
            audio_url = f"https://cdn1.suno.ai/{clip_id}.mp3"
            safe_title = safe_filename(title)
            out_path = OUTPUT_DIR / f"{idx:02d}-{safe_title}-{clip_id[:8]}.mp3"
            
            req = urllib.request.Request(audio_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(out_path, 'wb') as f:
                    while True:
                        chunk = resp.read(64 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
            
            size = out_path.stat().st_size
            print(f"  ✓ saved {out_path.name} ({size:,} bytes)")
            
            results.append({
                'index': idx,
                'clip_id': clip_id,
                'title': title,
                'audio_url': audio_url,
                'model': f'v{model}',
                'duration_seconds': duration,
                'prompt': prompt,
                'file': str(out_path),
                'size_bytes': size,
            })
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({'url': url, 'error': str(e)})
    
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n✓ Manifest saved to {manifest_path}")
    success = sum(1 for r in results if 'file' in r)
    total_dur = sum(r.get('duration_seconds', 0) for r in results if 'duration_seconds' in r)
    print(f"=== Summary: {success}/{len(results)} tracks downloaded, total {total_dur:.1f}s = {total_dur/60:.1f}min ===")
    print(f"\nNext step: pass URLs of remaining tracks if any")


if __name__ == "__main__":
    main(sys.argv[1:])
