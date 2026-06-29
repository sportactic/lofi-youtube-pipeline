#!/usr/bin/env python3
"""Upload video to channel with optimized title/description"""
import os, sys, json, argparse, asyncio
from datetime import datetime, timezone, timedelta

# Channel configs
CHANNELS = {
    'thelofi': {
        'name': 'TheLoFi',
        'method': 'youtube-direct',
        'channel_id': 'UCpdnbfS3UL-_bKr_8uJGYxQ',
        'secrets': ['YOUTUBE_REFRESH_TOKEN', 'YOUTUBE_CLIENT_SECRETS_JSON'],
        'monetize': False,
        'category_id': '10',  # Music
    },
    'lofinippon': {
        'name': 'LofiNippon',
        'method': 'youtube-direct',
        'channel_id': 'UCEXLQ3tlpMu4TWnHojfEP7g',
        'secrets': ['YOUTUBE_NIPPON_REFRESH_TOKEN', 'YOUTUBE_NIPPON_CLIENT_SECRETS_JSON'],
        'monetize': False,
        'category_id': '10',
    },
    'flychill': {
        'name': 'FlyChill',
        'method': 'zernio',
        'channel_id': 'UCvnQnOtZUJ9ZsM1ZgJpvBqQ',
        'secrets': ['ZERNIO_API_KEY'],
        'monetize': True,
        'category_id': '10',
    },
}

# Top 5 most spoken languages (besides English)
# Source: Ethnologue 2025 - English, Mandarin, Hindi, Spanish, French, Arabic, Bengali
# For YouTube reach: English + Mandarin + Hindi + Spanish + Arabic (covers 50%+ of world)
TOP_LANGS = ['es', 'zh', 'hi', 'ar', 'fr']

# Title templates by channel mood
TITLES = {
    'thelofi': [
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
    'lofinippon': [
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
    'flychill': [
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
}

DESCRIPTIONS_EN = {
    'thelofi': """🌧️ Cozy Lofi Hip Hop for studying, sleeping, and unwinding

1 hour of warm, melancholic lofi beats featuring rain on windows, soft piano, vinyl crackle, and the quiet intimacy of a late-night study session. Let this mix be your companion for focus and calm.

🌙 What's inside:
• Rain ambience
• Warm lamp lighting
• Soft piano & jazzy chords
• Cozy room atmosphere
• Vinyl crackle texture

☕ Best for:
• Deep work & studying
• Late-night relaxation
• Sleep & meditation
• Reading & writing
• Quiet coffee shop vibes

🎧 Headphones recommended for the full audio experience.

© 2026 TheLoFi · Original compositions
""",
    'lofinippon': """🌸 Japanese Lofi Hip Hop for studying, sleeping, and unwinding

1 hour of serene, traditional Japanese-inspired lofi beats. Lantern light, sakura petals, tatami rooms, and the peaceful sound of bamboo rain. A journey through Japanese aesthetics.

🌙 What's inside:
• Sakura petals ambience
• Paper lantern glow
• Koto & traditional Japanese instruments
• Bamboo rain texture
• Tatami room atmosphere

☕ Best for:
• Meditation & zen
• Studying & focus
• Sleep & relaxation
• Tea ceremony ambience
• Anime watching

🎧 Headphones recommended for the full audio experience.

© 2026 LofiNippon · Original compositions
""",
    'flychill': """🌃 Chill Lofi Hip Hop for studying, sleeping, and unwinding

1 hour of urban, melancholic lofi beats. Rain-streaked windows, city bokeh lights, soft piano, and the contemplative mood of late-night cityscape views. Find your moment of calm.

🌙 What's inside:
• Rain on glass texture
• City lights bokeh
• Soft piano & ambient pads
• Late-night urban atmosphere
• Contemplative mood

☕ Best for:
• Late-night focus
• Studying & deep work
• Sleep & relaxation
• Reading & writing
• Coding sessions

🎧 Headphones recommended for the full audio experience.

© 2026 FlyChill · Original compositions
""",
}

TAGS = {
    'thelofi': ['lofi', 'lo-fi', 'lofi hip hop', 'chill beats', 'study music', 'sleep music', 'rain sounds', 'cozy room', 'late night', 'relaxing music', 'chillhop', 'lofi mix', '1 hour lofi', 'study beats', 'focus music', 'calm music', 'melancholic', 'piano lofi', 'jazz lofi', 'vinyl crackle'],
    'lofinippon': ['lofi', 'lo-fi', 'japanese lofi', '和風', '和ロフィー', 'study music', 'sleep music', 'sakura', 'lantern', 'tatami', 'zen music', 'chill beats', 'relaxing music', 'bamboo rain', 'japanese aesthetic', 'anime lofi', 'koto', 'tea ceremony', 'meditation', 'calm music'],
    'flychill': ['lofi', 'lo-fi', 'chill beats', 'study music', 'sleep music', 'rain music', 'city lofi', 'urban chill', 'chillhop', 'late night', 'melancholic', 'city lights', 'bokeh', 'relaxing music', 'focus music', '1 hour lofi', 'deep focus', 'coding music', 'rainy window', 'contemplative'],
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('channel', choices=list(CHANNELS.keys()))
    parser.add_argument('video', help='Path to video file')
    parser.add_argument('--publish-at', help='ISO 8601 datetime (UTC)')
    parser.add_argument('--title', help='Override title')
    parser.add_argument('--privacy', default='private', choices=['private', 'unlisted', 'public'])
    args = parser.parse_args()
    
    cfg = CHANNELS[args.channel]
    print(f'Channel: {cfg["name"]} ({args.channel})')
    print(f'Method: {cfg["method"]}')
    print(f'Monetize: {cfg["monetize"]}')
    print(f'Video: {args.video}')
    print(f'Publish at: {args.publish_at}')
    
    # Pick a title (user can override)
    import random
    title = args.title or random.choice(TITLES[args.channel])
    print(f'Title: {title}')
    
    # Description: English + 5 languages
    desc_en = DESCRIPTIONS_EN[args.channel]
    print(f'Description (EN): {len(desc_en)} chars')
    
    # TODO: Translate to top 5 languages
    # For now, use English
    
    # TODO: Actual upload via YouTube API or Zernio
    # This is the next step

if __name__ == '__main__':
    main()
