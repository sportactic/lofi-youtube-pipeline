#!/usr/bin/env python3
"""Render video from manifest - concatenates visuals + loops audio"""
import os, sys, json, glob, subprocess, shutil
import urllib.request

def download_file(url, dest):
    if os.path.exists(dest):
        return
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Authorization': f'Bearer {open("/workspace/suno-jwt.txt").read().strip()}',
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        with open(dest, 'wb') as f:
            shutil.copyfileobj(r, f)

def get_audio_duration(path):
    try:
        out = subprocess.check_output([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', path
        ]).decode().strip()
        return float(out)
    except: return 0

def main():
    channel = sys.argv[1] if len(sys.argv) > 1 else 'thelofi'
    loops = int(sys.argv[2]) if len(sys.argv) > 2 else 3  # default 3 loops
    
    # Load manifest
    with open(f'/workspace/daily-pipeline/manifest-{channel}.json') as f:
        manifest = json.load(f)
    
    tracks = manifest['tracks']
    visuals_dir = manifest['visuals_dir']
    
    # Find visuals
    visuals = sorted(glob.glob(f'{visuals_dir}/*.png') + glob.glob(f'{visuals_dir}/*.jpg'))
    if not visuals:
        print(f'ERROR: No visuals in {visuals_dir}')
        sys.exit(1)
    
    # Download all tracks
    audio_dir = f'/workspace/daily-pipeline/audio-{channel}'
    os.makedirs(audio_dir, exist_ok=True)
    
    print(f'{channel}: {len(tracks)} tracks × {loops} loops')
    print(f'  Visuals: {len(visuals)} images')
    print(f'  Downloading tracks...')
    
    for t in tracks:
        dest = f'{audio_dir}/{t["id"]}.mp3'
        if not os.path.exists(dest):
            download_file(t['audio_url'], dest)
    
    # Build video.txt (concat list for visuals)
    video_concat = '/workspace/daily-pipeline/video_concat.txt'
    with open(video_concat, 'w') as f:
        # Each visual shown for same duration as its track
        for i, t in enumerate(tracks):
            visual = visuals[i % len(visuals)]
            dur = get_audio_duration(f'{audio_dir}/{t["id"]}.mp3')
            f.write(f"file '{visual}'\n")
            f.write(f"duration {dur:.3f}\n")
        # Last visual (ffmpeg concat requirement)
        f.write(f"file '{visuals[(len(tracks)) % len(visuals)]}'\n")
    
    # Build audio concat (loops)
    audio_concat = '/workspace/daily-pipeline/audio_concat.txt'
    with open(audio_concat, 'w') as f:
        for _ in range(loops):
            for t in tracks:
                f.write(f"file '{audio_dir}/{t['id']}.mp3'\n")
    
    # Render video (no audio first)
    video_only = f'/workspace/daily-pipeline/video-{channel}-only.mp4'
    print(f'  Rendering video-only...')
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', video_concat,
        '-vsync', 'vfr', '-pix_fmt', 'yuv420p',
        '-vf', 'scale=1280:720,fps=12', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-movflags', '+faststart',
        video_only
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Concatenate audio (with loops)
    audio_concat_mp3 = f'/workspace/daily-pipeline/audio-{channel}.mp3'
    print(f'  Concatenating audio ({loops} loops)...')
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', audio_concat,
        '-c', 'copy',
        audio_concat_mp3
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Mux final video
    final_video = f'/workspace/daily-pipeline/video-{channel}.mp4'
    print(f'  Muxing final video...')
    cmd = [
        'ffmpeg', '-y', '-i', video_only, '-i', audio_concat_mp3,
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
        '-shortest', '-movflags', '+faststart',
        final_video
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Get final duration
    duration = get_audio_duration(audio_concat_mp3)
    size_mb = os.path.getsize(final_video) / 1024 / 1024
    print(f'  ✓ Final video: {final_video}')
    print(f'    Duration: {duration:.0f}s = {duration/60:.1f} min')
    print(f'    Size: {size_mb:.0f} MB')

if __name__ == '__main__':
    main()
