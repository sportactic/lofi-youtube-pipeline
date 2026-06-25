#!/usr/bin/env python3
"""Interactive OAuth for @lofinippon — paste-back flow.

The mavis sandbox has no browser, so:
1. This script prints the Google auth URL
2. User opens URL in their browser, signs in with @lofinippon Google account
3. Google redirects to http://localhost (the OAuth redirect URI)
4. The browser will show "site not reachable" (since we have no server) BUT
   the URL in the address bar contains the auth code
5. User copies the FULL URL (or just the code) and pastes back
6. This script exchanges code for tokens
7. Saves refresh_token to mavis secret YOUTUBE_NIPPON_REFRESH_TOKEN

Usage:
  python3 oauth-interactive.py
  # prints URL → user pastes back redirect URL → script saves token
"""
import os, sys, json, secrets, hashlib, base64, requests

# Load client_secrets from mavis secret (passed as env var by caller)
client_secrets_raw = os.environ['YOUTUBE_NIPPON_CLIENT_SECRETS_JSON']
client_secrets = json.loads(client_secrets_raw)
CLIENT_ID = client_secrets['installed']['client_id']
CLIENT_SECRET = client_secrets['installed']['client_secret']
REDIRECT_URI = client_secrets['installed']['redirect_uris'][0]
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl', 'https://www.googleapis.com/auth/youtube']

# PKCE
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()

auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + '&'.join([
    f'client_id={CLIENT_ID}',
    f'redirect_uri={REDIRECT_URI}',
    'response_type=code',
    f'scope={" ".join(SCOPES)}',
    f'code_challenge={code_challenge}',
    'code_challenge_method=S256',
    'access_type=offline',
    'prompt=consent',
])

print('=' * 70, file=sys.stderr)
print('@lofinippon OAuth — paste-back flow', file=sys.stderr)
print('=' * 70, file=sys.stderr)
print('', file=sys.stderr)
print('STEP 1: Open this URL in your browser:', file=sys.stderr)
print('', file=sys.stderr)
print(auth_url, file=sys.stderr)
print('', file=sys.stderr)
print('STEP 2: Sign in with the Google account that owns @lofinippon', file=sys.stderr)
print('STEP 3: Grant YouTube permissions', file=sys.stderr)
print('STEP 4: Google will redirect to http://localhost?...', file=sys.stderr)
print('        The page will fail to load, BUT the URL bar will contain a code.', file=sys.stderr)
print('STEP 5: Copy the FULL URL (or just the "code=..." part) and paste below.', file=sys.stderr)
print('', file=sys.stderr)

# Read paste-back from stdin
print('Paste the redirect URL (or just the code) and press Enter:', file=sys.stderr)
pasted = input('> ').strip()

if not pasted:
    print('ERROR: empty input', file=sys.stderr)
    sys.exit(1)

# Extract code from URL or raw
from urllib.parse import urlparse, parse_qs
code = None
if pasted.startswith('http'):
    q = parse_qs(urlparse(pasted).query)
    code = q.get('code', [None])[0]
else:
    code = pasted

if not code:
    print('ERROR: no code found in input', file=sys.stderr)
    sys.exit(1)

print(f'\nGot code: {code[:20]}...', file=sys.stderr)
print('Exchanging for tokens...', file=sys.stderr)

# Exchange code for tokens
token_resp = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': code,
    'code_verifier': code_verifier,
    'grant_type': 'authorization_code',
    'redirect_uri': REDIRECT_URI,
})
if token_resp.status_code != 200:
    print(f'ERROR: {token_resp.status_code} {token_resp.text}', file=sys.stderr)
    sys.exit(1)
tokens = token_resp.json()

print(f'\n=== TOKENS RECEIVED ===', file=sys.stderr)
print(f'  access_token:  {tokens.get("access_token", "MISSING")[:40]}...', file=sys.stderr)
print(f'  refresh_token: {tokens.get("refresh_token", "MISSING")[:40]}...', file=sys.stderr)
print(f'  expires_in:    {tokens.get("expires_in")}', file=sys.stderr)
print(f'  scope:         {tokens.get("scope")}', file=sys.stderr)

# Save tokens to local file
with open('/workspace/lofinippon-pipeline/token-nippon.json', 'w') as f:
    json.dump({
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': ' '.join(SCOPES),
    }, f, indent=2)
print(f'\nSaved tokens to /workspace/lofinippon-pipeline/token-nippon.json', file=sys.stderr)

# Verify which channels this token has access to
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
creds = Credentials(
    token=tokens['access_token'],
    refresh_token=tokens['refresh_token'],
    token_uri='https://oauth2.googleapis.com/token',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=SCOPES,
)
youtube = build('youtube', 'v3', credentials=creds)
resp = youtube.channels().list(part='id,snippet', mine=True).execute()
print(f'\n=== Channels accessible with this token ===', file=sys.stderr)
for ch in resp.get('items', []):
    print(f"  ID: {ch['id']} | {ch['snippet']['title']} | {ch['snippet'].get('customUrl', 'no handle')}", file=sys.stderr)

# Output for caller to capture
print(json.dumps({
    'refresh_token': tokens['refresh_token'],
    'channels': [{'id': ch['id'], 'title': ch['snippet']['title']} for ch in resp.get('items', [])],
}))