#!/usr/bin/env python3
"""Prepare individual albums for each recent video"""
import os, sys, json

# Recent videos with their metadata
RECENT_VIDEOS = {
    'thelofi': {
        'HuaUcIvsBzU': {
            'title': '1 Hour+ Cozy Lofi Vibes to Sleep Study Focus | Late Night Rainy Window Desk',
            'date': '2026-06-28',
            'album_name': 'Cozy Hours Vol 3 — Late Night Session',
            'album_description': 'A late-night study mix of warm lofi beats. Recorded during midnight rain.',
            'mood': 'late_night_warm',
        },
        'dWKkNIjl0ZQ': {
            'title': '1 Hour+ Cozy Lofi Vibes Beats to Sleep Study Focus | Anime Girl and Chameleon',
            'date': '2026-06-25',
            'album_name': 'Cozy Hours Vol 3 — Anime Cozy Session',
            'album_description': 'Studio lofi mix featuring warm piano and cozy vinyl crackle.',
            'mood': 'afternoon_warm',
        },
        'b-KqcNGuW3E': {
            'title': '1 Hour Smooth Rainy Lo-Fi Beats to Sleep, Study & Focus | Rain Sounds',
            'date': '2026-06-24',
            'album_name': 'Cozy Hours Vol 3 — Rainy Day',
            'album_description': 'Smooth rainy lofi beats with soft piano and rain ambience.',
            'mood': 'rainy_calm',
        },
        'SEF4f2SNgNI': {
            'title': 'Lofi Hip Hop Beats to Study, Sleep & Relax | Rainy Window & Coffee Vibes',
            'date': '2026-06-29',
            'album_name': 'Cozy Hours Vol 1 — Rainy Window',
            'album_description': 'Warm lofi beats with rain on the window and coffee.',
            'mood': 'evening_warm',
        },
        'CX6rdBybflU': {
            'title': 'Lofi Chill Beats | Rainy Window, Coffee & Quiet Study Night',
            'date': '2026-06-29',
            'album_name': 'Cozy Hours Vol 2 — Coffee & Pages',
            'album_description': 'Quiet late-night lofi for deep focus.',
            'mood': 'late_night_cozy',
        },
    },
    'lofinippon': {
        'WhhStj51U74': {
            'title': '1 Hour Japanese Lo-Fi Mix for Sleep and Study',
            'date': '2026-06-28',
            'album_name': 'Matsuri Dreams Vol 2 — Night Lanterns',
            'album_description': 'Quiet Japanese lofi for sleep and study.',
            'mood': 'zen_evening',
        },
        'mNgeBtWHgtA': {
            'title': '1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, Zen Garden',
            'date': '2026-06-27',
            'album_name': 'Matsuri Dreams Vol 1 — Sakura Garden',
            'album_description': 'Sakura garden themed Japanese lofi mix.',
            'mood': 'zen_garden',
        },
        'KTAC886oDWg': {
            'title': '1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, Zen Garden',
            'date': '2026-06-26',
            'album_name': 'Matsuri Dreams Vol 1 — Sakura Garden (Alternate)',
            'album_description': 'Sakura garden themed Japanese lofi mix.',
            'mood': 'zen_garden_alt',
        },
        'WNk1mx0AU2U': {
            'title': '1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, Tanuki',
            'date': '2026-06-29',
            'album_name': 'Matsuri Dreams Vol 3 — Tanuki Nights',
            'album_description': 'Mischievous tanuki inspired lofi mix.',
            'mood': 'tanuki_playful',
        },
        '4WIfrWLWlk0': {
            'title': '1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Tanuki, Lantern',
            'date': '2026-06-29',
            'album_name': 'Matsuri Dreams Vol 4 — Lantern Stroll',
            'album_description': 'Lantern stroll themed nighttime lofi mix.',
            'mood': 'lantern_walk',
        },
    },
    'flychill': {
        '6a419d6b8321bc6c307b2e05': {
            'title': 'FlyChill • 90 Min+ Cozy Lofi Beats to Study Sleep Relax',
            'date': '2026-06-29',
            'album_name': 'Late Hours Vol 1 — Cozy Sessions',
            'album_description': '90 minute cozy lofi mix.',
            'mood': 'cozy_long',
        },
        '6a415905d6ab8b16f96e7893': {
            'title': 'FlyChill • 1 Hour+ Lofi Beats to Study Sleep Relax | Cozy Rainy',
            'date': '2026-06-28',
            'album_name': 'Late Hours Vol 2 — Rainy Cozy',
            'album_description': 'Rainy window lofi.',
            'mood': 'rainy',
        },
        '6a41410395971128bd1e2f8c': {
            'title': 'FlyChill Lofi Mix',
            'date': '2026-06-28',
            'album_name': 'Late Hours Vol 3 — Silent Night',
            'album_description': 'Unnamed late night mix.',
            'mood': 'mystery',
        },
        '6a40a75a62ab75e93ac9b340': {
            'title': 'FlyChill • 1 Hour+ Lofi Beats to Study Sleep Relax | Rainy Mood',
            'date': '2026-06-28',
            'album_name': 'Late Hours Vol 4 — Rainy Mood',
            'album_description': 'Rainy mood lofi.',
            'mood': 'rainy_mood',
        },
    },
}

# Get existing track names for each channel
def get_tracks_for_channel(channel):
    try:
        with open(f'/workspace/distrokid/{channel}-tracks.json') as f:
            return json.load(f)
    except:
        return []

# Create album folder per video
output_root = '/workspace/distrokid/per-video-albums'
os.makedirs(output_root, exist_ok=True)

for channel, videos in RECENT_VIDEOS.items():
    tracks = get_tracks_for_channel(channel)
    
    # Get unique track names
    unique_names = []
    seen = set()
    for t in tracks:
        if t['new_name'] not in seen:
            seen.add(t['new_name'])
            unique_names.append(t['new_name'])
    
    for vid, info in videos.items():
        vid_dir = f"{output_root}/{channel}_{vid}"
        os.makedirs(vid_dir, exist_ok=True)
        
        # Album metadata
        album = {
            'video_id': vid,
            'channel': channel,
            'video_title': info['title'],
            'video_date': info['date'],
            'album_name': info['album_name'],
            'album_description': info['album_description'],
            'mood': info['mood'],
            'artist': {
                'thelofi': 'TheLoFi',
                'lofinippon': 'LofiNippon',
                'flychill': 'FlyChill',
            }[channel],
            'genre': 'Lo-Fi Hip Hop' if channel != 'lofinippon' else 'Japanese Lo-Fi',
            'tracks': [{'order': i+1, 'name': name} for i, name in enumerate(unique_names)],
            'total_tracks': len(unique_names),
        }
        
        with open(f'{vid_dir}/album.json', 'w') as f:
            json.dump(album, f, indent=2, ensure_ascii=False)
        
        print(f"  {channel}/{vid}: {info['album_name']}")

