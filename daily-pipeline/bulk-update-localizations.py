#!/usr/bin/env python3
"""
Bulk-update localizations on existing YouTube videos.
Uses the CORRECT format (localizations at TOP LEVEL).
"""
import os, sys, json, urllib.request, urllib.parse
import urllib.error

def get_token(rt, cid, cs):
    data = urllib.parse.urlencode({
        'client_id': cid, 'client_secret': cs,
        'refresh_token': rt, 'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['access_token']

def get_video(vid, token):
    """Get current snippet including defaultLanguage"""
    req = urllib.request.Request(
        f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid}',
        headers={'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)['items'][0]['snippet']

def update_localizations(token, vid, locs):
    """PUT update with localizations at TOP LEVEL"""
    snip = get_video(vid, token)
    
    body = {
        'id': vid,
        'snippet': {
            'categoryId': snip.get('categoryId', '10'),
            'defaultLanguage': snip.get('defaultLanguage') or 'en',
            'title': snip['title'],
            'description': snip['description'],
            'tags': snip.get('tags', []),
        },
        'localizations': locs
    }
    
    req = urllib.request.Request(
        'https://www.googleapis.com/youtube/v3/videos?part=snippet,localizations',
        data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json; charset=UTF-8'},
        method='PUT'
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

# Channel-specific translations
TRANSLATIONS = {
    'thelofi': {
        'es': {
            'title': '1 Hora de Lofi Beats para Estudiar, Dormir y Relajarse | Vibras de Lluvia',
            'description': '🌧️ Lofi Hip Hop acogedor para estudiar, dormir y desconectar.\n\n1 hora de ritmos lofi cálidos y melancólicos con lluvia en ventanas, piano suave, crujido de vinilo.\n\n☕ Ideal para: trabajo profundo, estudio, relajación nocturna, lectura, sueño.\n\n#Lofi #MusicaParaEstudiar #ChillBeats #Lluvia'
        },
        'zh-Hans': {
            'title': '1小时 Lofi 音乐 学习 睡眠 放松 | 舒适雨夜氛围',
            'description': '🌧️ 舒适的 Lofi Hip Hop,适合学习、睡眠和放松。\n\n1小时温暖、忧郁的 lofi 节拍,雨声、柔和的钢琴、黑胶唱片的噼啪声。\n\n☕ 适合:深度工作、学习、深夜放松、睡眠冥想。\n\n#Lofi #学习音乐 #ChillBeats'
        },
        'hi': {
            'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद और आराम',
            'description': '🌧️ पढ़ाई, सोने और आराम के लिए आरामदायक Lofi Hip Hop।\n\n1 घंटे के गर्म, उदास lofi बीट्स।\n\n☕ गहरा काम, पढ़ाई, देर रात आराम, नींद।\n\n#Lofi #स्टडीम्यूज़िक #चिलबीट्स'
        },
        'ar': {
            'title': 'ساعة من موسيقى Lofi للدراسة والنوم والاسترخاء',
            'description': '🌧️ موسيقى Lofi Hip Hop مريحة للدراسة والنوم والاسترخاء.\n\nساعة من إيقاعات lofi دافئة وحزينة مع المطر على النوافذ والبيانو الناعم.\n\n☕ مناسب لـ: العمل العميق، الدراسة، الاسترخاء الليلي، النوم.\n\n#Lofi #موسيقى_الدراسة #تشيل_بيتس'
        },
        'fr': {
            'title': '1 Heure de Beats Lofi pour Étudier, Dormir & Se Détendre',
            'description': '🌧️ Lofi Hip Hop cosy pour étudier, dormir et se détendre.\n\n1 heure de beats lofi chaleureux et mélancoliques.\n\n☕ Parfait pour: travail profond, études, détente nocturne, sommeil.\n\n#Lofi #MusiqueÉtude #ChillBeats'
        },
    },
    'lofinippon': {
        'es': {
            'title': '1 Hora de Lofi Beats para Estudiar, Dormir | Noche de Cerezos',
            'description': '🌸 Lofi Hip Hop japonés para estudiar, dormir y desconectar.\n\n1 hora de serenos beats lofi inspirados en Japón tradicional.\n\n#Lofi #LofiJapones #Sakura #MusicaParaEstudiar'
        },
        'zh-Hans': {
            'title': '1小时 Lofi 音乐 学习 睡眠 | 日式樱花之夜',
            'description': '🌸 日式 Lofi Hip Hop,适合学习、睡眠和放松。\n\n1小时宁静、传统的日式 lofi 节拍。灯笼光、樱花瓣、榻榻米房间,以及竹林雨的宁静之声。\n\n#Lofi #日式Lofi #樱花 #学习音乐'
        },
        'hi': {
            'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद | जापानी साकुरा रात',
            'description': '🌸 जापानी Lofi Hip Hop, पढ़ाई, सोने के लिए।\n\n1 घंटे के शांत, पारंपरिक जापानी-प्रेरित lofi बीट्स।\n\n#Lofi #जापानी_लोफी #साकुरा'
        },
        'ar': {
            'title': 'ساعة من موسيقى Lofi للدراسة والنوم | ليلة يابانية',
            'description': '🌸 موسيقى Lofi Hip Hop يابانية للدراسة والنوم.\n\nساعة من إيقاعات lofi الهادئة المستوحاة من اليابان التقليدية.\n\n#Lofi #لوفي_ياباني #ساكورا'
        },
        'fr': {
            'title': '1 Heure de Beats Lofi pour Étudier, Dormir | Nuit Japonaise',
            'description': '🌸 Lofi Hip Hop japonais pour étudier, dormir et se détendre.\n\n1 heure de beats lofi sereins inspirés du Japon traditionnel.\n\n#Lofi #LofiJaponais #Sakura #MusiqueÉtude'
        },
    },
}

# Videos to update per channel
VIDEOS_TO_UPDATE = {
    'thelofi': [
        'HuaUcIvsBzU',
        'dWKkNIjl0ZQ',
        'b-KqcNGuW3E',
        'SEF4f2SNgNI',
        'CX6rdBybflU',  # Already has localizations, will overwrite (same content)
    ],
    'lofinippon': [
        'WhhStj51U74',
        'mNgeBtWHgtA',
        'KTAC886oDWg',
        'WNk1mx0AU2U',
        '4WIfrWLWlk0',  # Already has localizations
    ],
}

def main():
    if len(sys.argv) > 1:
        channel = sys.argv[1]
    else:
        channel = 'thelofi'
    
    if channel == 'thelofi':
        cs = json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON'])
        cfg = {'rt': os.environ['YOUTUBE_REFRESH_TOKEN'],
               'cid': cs['installed']['client_id'], 'cs': cs['installed']['client_secret']}
    elif channel == 'lofinippon':
        cs = json.load(open('/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json'))
        cfg = {'rt': os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN'],
               'cid': cs['installed']['client_id'], 'cs': cs['installed']['client_secret']}
    else:
        print(f'Unknown channel: {channel}')
        sys.exit(1)
    
    token = get_token(cfg['rt'], cfg['cid'], cfg['cs'])
    locs = TRANSLATIONS[channel]
    videos = VIDEOS_TO_UPDATE[channel]
    
    print(f'=== Bulk Updating Localizations for {channel} ===')
    print(f'  Videos: {len(videos)}')
    print(f'  Languages: {", ".join(locs.keys())}')
    print()
    
    success = 0
    for vid in videos:
        try:
            update_localizations(token, vid, locs)
            print(f'  ✓ {vid}: Updated with {len(locs)} languages')
            success += 1
        except Exception as e:
            print(f'  ✗ {vid}: FAILED - {e}')
    
    print(f'\n{success}/{len(videos)} videos updated')
    print('\nVerify with: hl parameter on GET')
    print(f'  curl "...videos?part=snippet&hl=es&id={videos[0]}"')

if __name__ == '__main__':
    main()
