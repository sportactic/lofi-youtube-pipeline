#!/usr/bin/env python3
"""Properly update defaultLanguage + localizations"""
import os, sys, json, urllib.request, urllib.parse

def get_token(rt, cid, cs):
    data = urllib.parse.urlencode({
        'client_id': cid, 'client_secret': cs,
        'refresh_token': rt, 'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['access_token']

LOCS = {
    'thelofi': {
        'es': {'title': '1 Hora de Lofi Beats para Estudiar, Dormir y Relajarse | Vibras de Lluvia',
               'description': '🌧️ Lofi Hip Hop acogedor para estudiar, dormir y desconectar.\n\n#Lofi #MusicaParaEstudiar'},
        'zh-Hans': {'title': '1小时 Lofi 音乐 学习 睡眠 放松',
                    'description': '🌧️ 舒适的 Lofi Hip Hop,适合学习、睡眠和放松。\n\n#Lofi #学习音乐'},
        'hi': {'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद और आराम',
               'description': '🌧️ पढ़ाई, सोने और आराम के लिए Lofi Hip Hop।\n\n#Lofi #स्टडीम्यूज़िक'},
        'ar': {'title': 'ساعة من موسيقى Lofi للدراسة والنوم',
               'description': '🌧️ موسيقى Lofi Hip Hop مريحة للدراسة والنوم.\n\n#Lofi #موسيقى_الدراسة'},
        'fr': {'title': '1 Heure de Beats Lofi pour Étudier, Dormir & Se Détendre',
               'description': '🌧️ Lofi Hip Hop cosy pour étudier, dormir et se détendre.\n\n#Lofi #MusiqueÉtude'},
    },
    'lofinippon': {
        'es': {'title': '1 Hora de Lofi Beats para Estudiar, Dormir | Noche de Cerezos',
               'description': '🌸 Lofi Hip Hop japonés para estudiar y dormir.\n\n#Lofi #LofiJapones #Sakura'},
        'zh-Hans': {'title': '1小时 Lofi 音乐 学习 睡眠 | 日式樱花之夜',
                    'description': '🌸 日式 Lofi Hip Hop,适合学习、睡眠。\n\n#Lofi #日式Lofi #樱花'},
        'hi': {'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद | जापानी साकुरा',
               'description': '🌸 जापानी Lofi Hip Hop।\n\n#Lofi #जापानी_लोफी'},
        'ar': {'title': 'ساعة من موسيقى Lofi للدراسة | ليلة يابانية',
               'description': '🌸 موسيقى Lofi Hip Hop يابانية للدراسة.\n\n#Lofi #لوفي_ياباني'},
        'fr': {'title': '1 Heure de Beats Lofi pour Étudier, Dormir | Nuit Japonaise',
               'description': '🌸 Lofi Hip Hop japonais pour étudier et dormir.\n\n#Lofi #LofiJaponais'},
    },
}

def get_current(token, vid):
    """Get current title and description"""
    req = urllib.request.Request(
        f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid}',
        headers={'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as r:
        d = json.load(r)
    return d['items'][0]['snippet']

def update(token, vid, channel):
    """Update video with localizations + defaultLanguage"""
    snip = get_current(token, vid)
    
    body = {
        'id': vid,
        'snippet': {
            'title': snip['title'],  # Keep existing
            'description': snip['description'],  # Keep existing
            'categoryId': snip.get('categoryId', '10'),
            'defaultLanguage': 'en',
            'localizations': LOCS[channel],
        }
    }
    
    req = urllib.request.Request(
        'https://www.googleapis.com/youtube/v3/videos?part=snippet',
        data=json.dumps(body).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json; charset=UTF-8'},
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        return True
    except Exception as e:
        print(f'  ERROR: {e}')
        return False

if __name__ == '__main__':
    import sys
    channel = sys.argv[1]
    vids = sys.argv[2:]
    
    if channel == 'thelofi':
        cs = json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON'])
        cfg = {'rt': os.environ['YOUTUBE_REFRESH_TOKEN'],
               'cid': cs['installed']['client_id'], 'cs': cs['installed']['client_secret']}
    else:
        cs = json.load(open('/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json'))
        cfg = {'rt': os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN'],
               'cid': cs['installed']['client_id'], 'cs': cs['installed']['client_secret']}
    
    token = get_token(cfg['rt'], cfg['cid'], cfg['cs'])
    for vid in vids:
        ok = update(token, vid, channel)
        if ok:
            # Verify
            snip = get_current(token, vid)
            locs = list(snip.get('localizations', {}).keys())
            print(f'  ✓ {vid}: localizations={locs}')
        else:
            print(f'  ✗ {vid}: FAILED')
