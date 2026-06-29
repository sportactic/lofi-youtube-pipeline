#!/usr/bin/env python3
"""Bulk-update localizations on YouTube Shorts."""
import os, sys, json, urllib.request, urllib.parse

def get_token(rt, cid, cs):
    data = urllib.parse.urlencode({
        'client_id': cid, 'client_secret': cs,
        'refresh_token': rt, 'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['access_token']

def update(token, vid, locs):
    # Get current
    req = urllib.request.Request(
        f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={vid}',
        headers={'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as r:
        snip = json.load(r)['items'][0]['snippet']
    
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
        r.read()

# Short-specific translations (shorter descriptions)
SHORT_LOCS = {
    'thelofi': {
        'es': {'title': 'Lofi Acogedor para Estudiar 🌧️ | Descanso de 1 Min #Shorts',
               'description': '🎧 1 minuto de beats lofi acogedores. Lluvia + piano suave + luz cálida.\n\n#Lofi #ChillBeats #MusicaParaEstudiar'},
        'zh-Hans': {'title': '舒适 Lofi 学习 🌧️ | 1分钟休息 #Shorts',
                    'description': '🎧 1分钟舒适的 lofi 节拍。雨声 + 柔和钢琴 + 温暖的灯光。\n\n#Lofi #学习音乐'},
        'hi': {'title': 'आरामदायक Lofi पढ़ाई 🌧️ | 1 मिनट ब्रेक #Shorts',
               'description': '🎧 1 मिनट cozy lofi बीट्स। बारिश + मधुर पियानो।\n\n#Lofi #स्टडीम्यूज़िक'},
        'ar': {'title': 'Lofi مريح للدراسة 🌧️ | استراحة دقيقة #Shorts',
               'description': '🎧 دقيقة من beats lofi مريحة. مطر + بيانو ناعم.\n\n#Lofi #موسيقى_الدراسة'},
        'fr': {'title': 'Lofi Cosy pour Étudier 🌧️ | Pause 1 Min #Shorts',
               'description': '🎧 1 minute de beats lofi cosy. Pluie + piano doux.\n\n#Lofi #MusiqueÉtude'},
    },
    'lofinippon': {
        'es': {'title': 'Lofi Japonés 🌸 | 1 Min Zen #Shorts',
               'description': '🌸 1 minuto de Lofi Hip Hop japonés. Linternas + sakura.\n\n#Lofi #LofiJapones #Sakura'},
        'zh-Hans': {'title': '日式 Lofi 🌸 | 1分钟禅意 #Shorts',
                    'description': '🌸 1分钟日式 Lofi Hip Hop。灯笼 + 樱花。\n\n#Lofi #日式Lofi'},
        'hi': {'title': 'जापानी Lofi 🌸 | 1 मिनट ज़ेन #Shorts',
               'description': '🌸 1 मिनट जापानी Lofi Hip Hop। लालटेन + साकुरा।\n\n#Lofi #जापानी_लोफी'},
        'ar': {'title': 'لوفي ياباني 🌸 | 1 دقيقة زن #Shorts',
               'description': '🌸 دقيقة واحدة من Lofi ياباني. فوانيس + ساكورا.\n\n#Lofi #لوفي_ياباني'},
        'fr': {'title': 'Lofi Japonais 🌸 | 1 Min Zen #Shorts',
               'description': '🌸 1 minute de Lofi Hip Hop japonais. Lanternes + sakura.\n\n#Lofi #LofiJaponais'},
    },
}

# Shorts to update
THELOFI_SHORTS = ['x-bvNzurxgE', '2hz-qi-HGKs', '04EPcGe8wOk', 'THRIIATyNWU', 'AjkbZnvUa7Y']
LOFINIPPON_SHORTS = ['haV4-ecY4-k', 'U_r6ik0xoX8', 'Uy6rcny1ZRQ', 'KemSgoxkjCU']

def main():
    cs = json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON'])
    token = get_token(os.environ['YOUTUBE_REFRESH_TOKEN'], cs['installed']['client_id'], cs['installed']['client_secret'])
    
    print(f'=== TheLoFi Shorts ===')
    for vid in THELOFI_SHORTS:
        try:
            update(token, vid, SHORT_LOCS['thelofi'])
            print(f'  ✓ {vid}')
        except Exception as e:
            print(f'  ✗ {vid}: {e}')
    
    cs_n = json.load(open('/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json'))
    token_n = get_token(os.environ['YOUTUBE_NIPPON_REFRESH_TOKEN'], cs_n['installed']['client_id'], cs_n['installed']['client_secret'])
    
    print(f'\n=== LoFiNippon Shorts ===')
    for vid in LOFINIPPON_SHORTS:
        try:
            update(token_n, vid, SHORT_LOCS['lofinippon'])
            print(f'  ✓ {vid}')
        except Exception as e:
            print(f'  ✗ {vid}: {e}')

if __name__ == '__main__':
    main()
