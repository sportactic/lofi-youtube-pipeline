#!/usr/bin/env python3
"""
End-Screen Generator
Creates a 15-20 second outro with cross-promo to other channels.
Appends to end of main video.
"""
import os, sys, json, subprocess
from PIL import Image, ImageDraw, ImageFont

# Channel cross-promo map
CROSS_PROMO = {
    'thelofi': {
        'name': 'TheLoFi',
        'promote': [
            {'name': 'LofiNippon', 'handle': '@lofinippon', 'channel_id': 'UCEXLQ3tlpMu4TWnHojfEP7g', 'color': '#E91E63', 'tagline': 'Japanese Lofi'},
            {'name': 'FlyChill', 'handle': '@FlyChill', 'channel_id': 'UCvnQnOtZUJ9ZsM1ZgJpvBqQ', 'color': '#5E81F4', 'tagline': 'Urban Chill Lofi'},
        ],
    },
    'lofinippon': {
        'name': 'LofiNippon',
        'promote': [
            {'name': 'TheLoFi', 'handle': '@The-Lo-Fi', 'channel_id': 'UCpdnbfS3UL-_bKr_8uJGYxQ', 'color': '#FFA726', 'tagline': 'Cozy Western Lofi'},
            {'name': 'FlyChill', 'handle': '@FlyChill', 'channel_id': 'UCvnQnOtZUJ9ZsM1ZgJpvBqQ', 'color': '#5E81F4', 'tagline': 'Urban Chill Lofi'},
        ],
    },
    'flychill': {
        'name': 'FlyChill',
        'promote': [
            {'name': 'TheLoFi', 'handle': '@The-Lo-Fi', 'channel_id': 'UCpdnbfS3UL-_bKr_8uJGYxQ', 'color': '#FFA726', 'tagline': 'Cozy Western Lofi'},
            {'name': 'LofiNippon', 'handle': '@lofinippon', 'channel_id': 'UCEXLQ3tlpMu4TWnHojfEP7g', 'color': '#E91E63', 'tagline': 'Japanese Lofi'},
        ],
    },
}

def create_end_screen(channel, output_path, duration=18, width=1280, height=720, fps=12):
    cfg = CROSS_PROMO[channel]
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        big_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    except:
        title_font = small_font = big_font = ImageFont.load_default()
    
    for sec in range(duration):
        img = Image.new('RGB', (width, height), (15, 12, 25))
        draw = ImageDraw.Draw(img)
        
        # Background gradient
        for y in range(height):
            shade = int(20 * (1 - y / height))
            draw.line([(0, y), (width, y)], fill=(25 + shade, 20 + shade, 35 + shade))
        
        # Title
        thanks = "Thanks for Listening"
        bbox = draw.textbbox((0, 0), thanks, font=big_font)
        text_width = bbox[2] - bbox[0]
        draw.text(((width - text_width) // 2, 50), thanks, fill=(255, 255, 255), font=big_font)
        
        sub = "More from our channels ↓"
        bbox = draw.textbbox((0, 0), sub, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text(((width - text_width) // 2, 115), sub, fill=(200, 200, 200), font=small_font)
        
        # Two cross-promo cards
        for i, promo in enumerate(cfg['promote']):
            x_pos = (width // 2 - 460) if i == 0 else (width // 2 + 40)
            y_pos = 200
            card_w = 420
            card_h = 230
            
            draw.rounded_rectangle(
                [x_pos, y_pos, x_pos + card_w, y_pos + card_h],
                radius=12, fill=(30, 28, 40), outline=promo['color'], width=3
            )
            
            # Icon
            icon_radius = 45
            icon_cx = x_pos + 75
            icon_cy = y_pos + 90
            draw.ellipse(
                [icon_cx - icon_radius, icon_cy - icon_radius,
                 icon_cx + icon_radius, icon_cy + icon_radius],
                fill=promo['color']
            )
            first = promo['name'][0]
            bbox = draw.textbbox((0, 0), first, font=big_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            draw.text(
                (icon_cx - text_w // 2, icon_cy - text_h // 2 - 8),
                first, fill=(255, 255, 255), font=big_font
            )
            
            # Info
            draw.text((x_pos + 150, y_pos + 40), promo['name'], fill=(255, 255, 255), font=title_font)
            draw.text((x_pos + 150, y_pos + 80), promo['handle'], fill=promo['color'], font=small_font)
            draw.text((x_pos + 150, y_pos + 110), promo['tagline'], fill=(180, 180, 180), font=small_font)
            
            # Subscribe button
            btn_w = 180
            btn_h = 45
            btn_x = x_pos + 150
            btn_y = y_pos + 155
            draw.rounded_rectangle(
                [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
                radius=22, fill=promo['color']
            )
            btn_text = "SUBSCRIBE"
            bbox = draw.textbbox((0, 0), btn_text, font=title_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            draw.text(
                (btn_x + (btn_w - text_w) // 2, btn_y + (btn_h - text_h) // 2 - 6),
                btn_text, fill=(255, 255, 255), font=title_font
            )
        
        # Footer
        footer = f"{cfg['name']}  •  Press subscribe to never miss a beat"
        bbox = draw.textbbox((0, 0), footer, font=small_font)
        text_width = bbox[2] - bbox[0]
        draw.text(((width - text_width) // 2, 500), footer, fill=(150, 150, 150), font=small_font)
        
        frame_path = f'/tmp/endscreen-frame-{sec:03d}.png'
        img.save(frame_path)
    
    # Combine frames
    frame_pattern = '/tmp/endscreen-frame-%03d.png'
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', frame_pattern,
        '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-t', str(duration),
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    
    for sec in range(duration):
        try: os.remove(f'/tmp/endscreen-frame-{sec:03d}.png')
        except: pass

def append_end_screen(input_video, end_screen, output):
    concat_file = '/tmp/concat-endscreen.txt'
    with open(concat_file, 'w') as f:
        f.write(f"file '{input_video}'\n")
        f.write(f"file '{end_screen}'\n")
    
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart',
        output
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output

def main():
    if len(sys.argv) < 4:
        print('Usage: endscreen.py <channel> <input_video> <output_video> [duration]')
        sys.exit(1)
    
    channel = sys.argv[1]
    input_video = sys.argv[2]
    output_video = sys.argv[3]
    duration = int(sys.argv[4]) if len(sys.argv) > 4 else 18
    
    print(f'=== End-Screen for {channel} ===')
    end_screen = '/tmp/end-screen.mp4'
    print(f'  [1/2] Generating {duration}s end screen...')
    create_end_screen(channel, end_screen, duration=duration)
    print(f'    ✓ End screen: {end_screen} ({os.path.getsize(end_screen)/1024:.0f}KB)')
    
    print('  [2/2] Appending to main video...')
    append_end_screen(input_video, end_screen, output_video)
    print(f'    ✓ Final: {output_video} ({os.path.getsize(output_video)/1024/1024:.1f} MB)')

if __name__ == '__main__':
    main()
