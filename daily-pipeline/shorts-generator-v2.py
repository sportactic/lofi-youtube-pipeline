#!/usr/bin/env python3
"""
YouTube Shorts Generator v2 - UNIQUE visuals per Short
Each Short uses a different visual + different timing window.
Generates up to 6 shorts per video (one every 6 hours).
"""
import os, sys, json, subprocess, random, math
import urllib.request

def get_video_duration(path):
    out = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', path
    ]).decode().strip()
    return float(out)

def list_visuals(visuals_dir):
    """Get all visual files, sorted"""
    files = []
    for ext in ('png', 'jpg', 'jpeg'):
        files.extend(sorted([f'{visuals_dir}/{f}' for f in os.listdir(visuals_dir) if f.endswith(f'.{ext}')]))
    return files

def cut_short_unique(input_video, output_short, start_time, duration, visual_path):
    """
    Cut a 9:16 vertical short with a SPECIFIC visual.
    The visual replaces the video frames (single static image).
    """
    # Get input dimensions
    out = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0', input_video
    ]).decode().strip()
    w, h = map(int, out.split(','))
    
    # Use the visual image as a static background, cropped to 9:16
    # ffmpeg: loop image, crop center, scale to 1080x1920
    # Then add audio from the input video at the specified time
    
    # Get visual dimensions
    out = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0', visual_path
    ]).decode().strip()
    vw, vh = map(int, out.split(','))
    
    # Calculate crop for 9:16 from visual
    target_h = vh
    target_w = int(vh * 9 / 16)
    if target_w > vw:
        target_w = vw
        target_h = int(vw * 16 / 9)
    crop_x = (vw - target_w) // 2
    crop_y = (vh - target_h) // 2
    
    # Add subtle zoom-in animation for engagement (1.0x to 1.05x)
    zoompan = f"zoompan=z='min(zoom+0.0005,1.05)':d={int(duration*12)}:s=1080x1920:fps=12"
    
    vf = f"crop={target_w}:{target_h}:{crop_x}:{crop_y},scale=1080:1920,{zoompan}"
    
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1', '-i', visual_path,  # loop the visual image
        '-ss', str(start_time), '-t', str(duration),  # audio segment
        '-i', input_video,
        '-filter_complex', f'[0:v]{vf}[v]',
        '-map', '[v]', '-map', '1:a',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        '-movflags', '+faststart',
        output_short
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def cut_short_center_crop(input_video, output_short, start_time, duration):
    """
    Cut a 9:16 vertical short from the video itself (center crop).
    """
    out = subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'stream=width,height',
        '-of', 'csv=p=0', input_video
    ]).decode().strip()
    w, h = map(int, out.split(','))
    
    target_h = h
    target_w = int(h * 9 / 16)
    crop_x = (w - target_w) // 2
    
    vf = f"crop={target_w}:{h}:{crop_x}:0,scale=1080:1920"
    
    cmd = [
        'ffmpeg', '-y', '-ss', str(start_time), '-t', str(duration),
        '-i', input_video,
        '-vf', vf,
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        output_short
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def pick_unique_clips(video_path, num_clips=4, clip_duration=45):
    """Pick N start times spread across the video, each at unique position"""
    total = get_video_duration(video_path)
    usable = total - clip_duration - 30  # avoid first/last 15s
    if usable <= 0:
        return []
    
    if num_clips == 1:
        return [usable / 2]
    
    # Divide video into N+1 zones, pick center of each
    spacing = usable / num_clips
    times = []
    used_visuals = set()
    for i in range(num_clips):
        center = spacing * i + spacing / 2
        # Small random jitter
        center += random.uniform(-30, 30)
        center = max(15, min(center, total - clip_duration - 15))
        times.append(center)
    
    return times

def main():
    if len(sys.argv) < 4:
        print('Usage: shorts-generator-v2.py <channel> <video_path> <num_shorts> [visual_dir]')
        sys.exit(1)
    
    channel = sys.argv[1]
    video_path = sys.argv[2]
    num_shorts = int(sys.argv[3])
    visual_dir = sys.argv[4] if len(sys.argv) > 4 else f'/workspace/visuals-{channel.replace("thelofi", "thelofi")}-v3'
    
    # Map channel to visual dir
    visual_dirs = {
        'thelofi': '/workspace/visuals-thelofi-v3',
        'lofinippon': '/workspace/visuals-lofi-nippon-v3',
        'flychill': '/workspace/visuals-fly-chill-v3',
    }
    visual_dir = visual_dirs.get(channel, visual_dir)
    
    if not os.path.exists(video_path):
        print(f'Video not found: {video_path}')
        sys.exit(1)
    
    visuals = list_visuals(visual_dir)
    if not visuals:
        print(f'No visuals found in {visual_dir}')
        sys.exit(1)
    
    out_dir = f'/workspace/daily-pipeline/shorts-{channel}'
    os.makedirs(out_dir, exist_ok=True)
    
    # Cleanup old shorts
    for f in os.listdir(out_dir):
        os.remove(f'{out_dir}/{f}')
    
    print(f'=== Generating {num_shorts} UNIQUE Shorts for {channel} ===')
    print(f'  Source video: {video_path}')
    print(f'  Available visuals: {len(visuals)} unique images')
    print(f'  Output: {out_dir}/')
    
    # Pick unique time windows
    times = pick_unique_clips(video_path, num_shorts, clip_duration=45)
    print(f'  Time windows: {[f"{t:.0f}s" for t in times]}')
    
    # Pick unique visuals (round-robin through all available)
    selected_visuals = []
    for i in range(num_shorts):
        v = visuals[i % len(visuals)]
        selected_visuals.append(v)
    
    print(f'  Visuals used:')
    for i, (t, v) in enumerate(zip(times, selected_visuals)):
        vname = os.path.basename(v)
        print(f'    [{i+1}] t={t:.0f}s → {vname}')
    
    generated = []
    for i, (t, v) in enumerate(zip(times, selected_visuals)):
        out = f'{out_dir}/short-{i+1:02d}.mp4'
        print(f'\n  [{i+1}/{num_shorts}] Generating {out}...')
        print(f'    Visual: {os.path.basename(v)}')
        print(f'    Time: {t:.0f}s, Duration: 45s')
        
        # Use unique visual + crop from audio segment
        try:
            cut_short_unique(video_path, out, t, 45, v)
            size = os.path.getsize(out) / 1024 / 1024
            print(f'    ✓ {out} ({size:.1f} MB)')
            generated.append(out)
        except Exception as e:
            print(f'    ✗ Failed: {e}')
            # Fallback to center crop
            try:
                cut_short_center_crop(video_path, out, t, 45)
                size = os.path.getsize(out) / 1024 / 1024
                print(f'    ✓ (center crop fallback) {out} ({size:.1f} MB)')
                generated.append(out)
            except Exception as e2:
                print(f'    ✗ Center crop also failed: {e2}')
    
    print(f'\n=== {len(generated)}/{num_shorts} Shorts generated ===')
    for g in generated:
        print(f'  {g}')

if __name__ == '__main__':
    main()
