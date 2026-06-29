#!/usr/bin/env python3
"""
Add YouTube localizations (multi-language) to existing videos.
YouTube's API: PUT https://www.googleapis.com/youtube/v3/videos?part=localizations
with { id: VIDEO_ID, localizations: {es: {...}, zh-Hans: {...}, ...}}
"""
import os, sys, json, urllib.request, urllib.parse
import argparse

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

# Localizations for each channel
LOCALIZATIONS = {
    'thelofi': {
        'es': {
            'title': '1 Hora de Lofi Beats para Estudiar, Dormir y Relajarse | Vibras de Lluvia',
            'description': '🌧️ Lofi Hip Hop acogedor para estudiar, dormir y desconectar\n\n1 hora de ritmos lofi cálidos y melancólicos con lluvia en ventanas, piano suave, crujido de vinilo.\n\n☕ Ideal para: trabajo profundo, estudio, relajación nocturna, lectura, sueño.\n\n#Lofi #MusicaParaEstudiar #ChillBeats #Lluvia'
        },
        'zh-Hans': {
            'title': '1小时 Lofi 音乐 学习 睡眠 放松 | 舒适雨夜氛围',
            'description': '🌧️ 舒适的 Lofi Hip Hop,适合学习、睡眠和放松\n\n1小时温暖、忧郁的 lofi 节拍。\n\n#Lofi #学习音乐 #ChillBeats'
        },
        'hi': {
            'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद और आराम',
            'description': '🌧️ पढ़ाई, सोने और आराम के लिए आरामदायक Lofi Hip Hop\n\n#Lofi #स्टडीम्यूज़िक #चिलबीट्स'
        },
        'ar': {
            'title': 'ساعة من موسيقى Lofi للدراسة والنوم والاسترخاء',
            'description': '🌧️ موسيقى Lofi Hip Hop مريحة للدراسة والنوم\n\n#Lofi #موسيقى_الدراسة'
        },
        'fr': {
            'title': '1 Heure de Beats Lofi pour Étudier, Dormir & Se Détendre',
            'description': '🌧️ Lofi Hip Hop cosy pour étudier, dormir et se détendre\n\n1 heure de beats lofi chaleureux et mélancoliques.\n\n#Lofi #MusiqueÉtude #ChillBeats'
        },
    },
    'lofinippon': {
        'es': {
            'title': '1 Hora de Lofi Beats para Estudiar, Dormir | Noche de Cerezos',
            'description': '🌸 Lofi Hip Hop japonés para estudiar, dormir y desconectar\n\n1 hora de serenos beats lofi inspirados en Japón tradicional.\n\n#Lofi #LofiJapones #Sakura'
        },
        'zh-Hans': {
            'title': '1小时 Lofi 音乐 学习 睡眠 | 日式樱花之夜',
            'description': '🌸 日式 Lofi Hip Hop,适合学习、睡眠和放松\n\n1小时宁静、传统的日式 lofi 节拍。\n\n#Lofi #日式Lofi #樱花'
        },
        'hi': {
            'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद | जापानी साकुरा रात',
            'description': '🌸 जापानी Lofi Hip Hop, पढ़ाई, सोने और आराम के लिए\n\n#Lofi #जापानी_लोफी'
        },
        'ar': {
            'title': 'ساعة من موسيقى Lofi للدراسة والنوم | ليلة يابانية',
            'description': '🌸 موسيقى Lofi Hip Hop يابانية للدراسة والنوم\n\n#Lofi #لوفي_ياباني'
        },
        'fr': {
            'title': '1 Heure de Beats Lofi pour Étudier, Dormir | Nuit Japonaise',
            'description': '🌸 Lofi Hip Hop japonais pour étudier, dormir et se détendre\n\n#Lofi #LofiJaponais #Sakura'
        },
    },
}

def add_localizations(token, video_id, channel):
    """Add localizations to an existing video"""
    locs = LOCALIZATIONS.get(channel, {})
    if not locs:
        print(f'  No translations for {channel}')
        return False
    
    body = {
        'id': video_id,
        'localizations': locs,
    }
    
    req = urllib.request.Request(
        'https://www.googleapis.com/youtube/v3/videos?part=localizations',
        data=json.dumps(body).encode(),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=UTF-8',
        },
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.load(r)
        print(f'  ✓ {video_id}: Added {len(locs)} localizations ({", ".join(locs.keys())})')
        return True
    except urllib.error.HTTPError as e:
        print(f'  ✗ {video_id}: HTTP {e.code} - {e.read().decode()[:200]}')
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('channel', choices=['thelofi', 'lofinippon'])
    parser.add_argument('video_ids', nargs='+', help='Video IDs to add localizations to')
    args = parser.parse_args()
    
    if args.channel == 'thelofi':
        cs = json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON'])
        cfg = {
            'refresh_token': os.environ['YOUTUBE_REFRESH_TOKEN'],
            'client_id': cs['installed']['client_id'],
            'client_secret': cs['installed']['client_secret'],
        }
    elif args.channel == 'lofinippon':
        cs = json.load(open('/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json'))
        cfg = {
            'refresh_token': os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN'],
            'client_id': cs['installed']['client_id'],
            'client_secret': cs['installed']['client_secret'],
        }
    
    token = get_access_token(cfg['refresh_token'], cfg['client_id'], cfg['client_secret'])
    
    print(f'=== Adding localizations to {args.channel} videos ===')
    success = 0
    for vid in args.video_ids:
        if add_localizations(token, vid, args.channel):
            success += 1
    
    print(f'\n{success}/{len(args.video_ids)} videos updated with multi-language support')

if __name__ == '__main__':
    main()
