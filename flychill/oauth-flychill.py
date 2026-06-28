#!/usr/bin/env python3
"""Interactive OAuth for @FlyChill — paste-back flow.

The FlyChill OAuth client is a WEB app type (n8n-quirktag project),
not a desktop/installed app. We use the standard Google OAuth flow
with PKCE and override the redirect_uri to http://localhost for
local development.
"""
import os, sys, json, secrets, hashlib, base64, requests

# Load client_secrets from env var or file
client_secrets_raw = os.environ.get('FLYCHILL_CLIENT_SECRETS_JSON')
if not client_secrets_raw:
    with open('/workspace/flychill-pipeline/oauth-client.json') as f:
        client_secrets_raw = f.read()

client_secrets = json.loads(client_secrets_raw)

# Handle both "installed" (desktop) and "web" (web app) types
if 'web' in client_secrets:
    cfg = client_secrets['web']
elif 'installed' in client_secrets:
    cfg = client_secrets['installed']
else:
    raise RuntimeError("OAuth client must have 'web' or 'installed' key")

CLIENT_ID = cfg['client_id']
CLIENT_SECRET = cfg['client_secret']
# Use http://localhost as redirect_uri for paste-back flow
REDIRECT_URI = 'http://localhost'
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
print('@FlyChill OAuth — paste-back flow (WEB app type)', file=sys.stderr)
print('=' * 70, file=sys.stderr)
print('', file=sys.stderr)
print('STEP 1: Open this URL in your browser:', file=sys.stderr)
print('', file=sys.stderr)
print(auth_url, file=sys.stderr)
print('', file=sys.stderr)
print('STEP 2: Sign in with your @FlyChill Google account, then', file=sys.stderr)
print('        you will be redirected to http://localhost/?code=...&scope=...', file=sys.stderr)
print('        The browser will show "site not reachable" — that is OK.', file=sys.stderr)
print('        Copy the FULL URL from the address bar.', file=sys.stderr)
print('', file=sys.stderr)
print('STEP 3: Paste the FULL redirect URL here and press Enter:', file=sys.stderr)
print('> ', end='', file=sys.stderr)

redirect_url = input().strip()

# Extract code from URL
if 'code=' in redirect_url:
    code = redirect_url.split('code=')[1].split('&')[0]
else:
    code = redirect_url.strip()

# Exchange code for tokens
token_response = requests.post(
    'https://oauth2.googleapis.com/token',
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
    },
    timeout=30,
)
token_data = token_response.json()

if 'refresh_token' not in token_data:
    print('', file=sys.stderr)
    print('ERROR: No refresh_token in response', file=sys.stderr)
    print(json.dumps(token_data, indent=2), file=sys.stderr)
    sys.exit(1)

refresh_token = token_data['refresh_token']

# Save to local file
token_path = '/workspace/flychill-pipeline/token.json'
with open(token_path, 'w') as f:
    json.dump({
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'token_uri': 'https://oauth2.googleapis.com/token',
    }, f, indent=2)

output = {
    'refresh_token': refresh_token,
    'client_id': CLIENT_ID,
    'token_uri': 'https://oauth2.googleapis.com/token',
    'token_file': token_path,
}
print(json.dumps(output, indent=2))
