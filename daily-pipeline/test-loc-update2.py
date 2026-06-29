"""Test: Try updating an existing video's localizations the OFFICIAL way"""
import os, sys, json, urllib.request

def get_token(rt, cid, cs):
    data = urllib.parse.urlencode({
        'client_id': cid, 'client_secret': cs,
        'refresh_token': rt, 'grant_type': 'refresh_token',
    }).encode()
    req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)['access_token']

cs = json.loads(os.environ['YOUTUBE_CLIENT_SECRETS_JSON'])
token = get_token(os.environ['YOUTUBE_REFRESH_TOKEN'], cs['installed']['client_id'], cs['installed']['client_secret'])

# Get current snippet
req = urllib.request.Request(
    'https://www.googleapis.com/youtube/v3/videos?part=snippet&id=SEF4f2SNgNI',
    headers={'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(req) as r:
    cur = json.load(r)['items'][0]['snippet']

print(f'Current title: {cur["title"]}')
print(f'Current defaultLanguage: {cur.get("defaultLanguage", "NOT SET")}')

# Build update with FULL snippet including localizations
# Per YouTube docs: https://developers.google.com/youtube/v3/docs/videos/update
body = {
    'id': 'SEF4f2SNgNI',
    'snippet': {
        'title': cur['title'],
        'description': cur['description'],
        'categoryId': cur.get('categoryId', '10'),
        'tags': cur.get('tags', []),
        'defaultLanguage': 'en',
        'localizations': {
            'es': {
                'title': '1 Hora de Lofi Beats para Estudiar, Dormir y Relajarse',
                'description': '🌧️ Lofi Hip Hop acogedor para estudiar y dormir.\n\n#Lofi #MusicaParaEstudiar'
            },
            'zh-Hans': {
                'title': '1小时 Lofi 音乐 学习 睡眠',
                'description': '🌧️ 舒适的 Lofi Hip Hop,适合学习、睡眠。\n\n#Lofi #学习音乐'
            },
            'hi': {
                'title': '1 घंटे Lofi बीट्स - पढ़ाई, नींद',
                'description': '🌧️ पढ़ाई, सोने के लिए Lofi Hip Hop।\n\n#Lofi #स्टडीम्यूज़िक'
            },
            'ar': {
                'title': 'ساعة من موسيقى Lofi للدراسة',
                'description': '🌧️ موسيقى Lofi Hip Hop للدراسة.\n\n#Lofi #موسيقى_الدراسة'
            },
            'fr': {
                'title': '1 Heure de Beats Lofi pour Étudier',
                'description': '🌧️ Lofi Hip Hop cosy pour étudier.\n\n#Lofi #MusiqueÉtude'
            }
        }
    }
}

# Try with part=snippet AND part=localizations combined
req = urllib.request.Request(
    'https://www.googleapis.com/youtube/v3/videos?part=snippet,localizations',
    data=json.dumps(body).encode(),
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json; charset=UTF-8'},
    method='PUT'
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = r.read().decode()
        print(f'Status: {r.status}')
        # Parse response
        try:
            data = json.loads(resp)
            print(f'Response: {json.dumps(data, indent=2)[:600]}')
        except:
            print(f'Response (raw): {resp[:500]}')
except urllib.error.HTTPError as e:
    print(f'Error {e.code}: {e.read().decode()[:300]}')

# Now check if it persisted
print('\nChecking persistence...')
req = urllib.request.Request(
    'https://www.googleapis.com/youtube/v3/videos?part=snippet,localizations&id=SEF4f2SNgNI',
    headers={'Authorization': f'Bearer {token}'}
)
with urllib.request.urlopen(req) as r:
    after = json.load(r)['items'][0]['snippet']
print(f'After update localizations: {list(after.get("localizations", {}).keys())}')
