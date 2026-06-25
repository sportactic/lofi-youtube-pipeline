#!/usr/bin/env python3
"""OAuth flow for @lofinippon channel.

This is COMPLETELY SEPARATE from the @The-Lo-Fi OAuth flow.
Uses YOUTUBE_NIPPON_* secrets.

After user completes OAuth, the refresh token is saved to mavis secret
YOUTUBE_NIPPON_REFRESH_TOKEN (overwriting the PENDING_OAUTH_FLOW placeholder).
"""
import os, sys, json, secrets, hashlib, base64
from urllib.parse import urlencode, parse_qs, urlparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# Load client_secrets from mavis secret
client_secrets_raw = os.environ['YOUTUBE_NIPPON_CLIENT_SECRETS_JSON']
client_secrets = json.loads(client_secrets_raw)
CLIENT_ID = client_secrets['installed']['client_id']
CLIENT_SECRET = client_secrets['installed']['client_secret']
REDIRECT_URI = client_secrets['installed']['redirect_uris'][0]
SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.force-ssl']

# PKCE
code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode()
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()

# Save code_verifier for the exchange step
with open('/tmp/nippon_code_verifier.txt', 'w') as f:
    f.write(code_verifier)
print(f'✓ Saved code_verifier to /tmp/nippon_code_verifier.txt', file=sys.stderr)

auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
    'client_id': CLIENT_ID,
    'redirect_uri': REDIRECT_URI,
    'response_type': 'code',
    'scope': ' '.join(SCOPES),
    'code_challenge': code_challenge,
    'code_challenge_method': 'S256',
    'access_type': 'offline',
    'prompt': 'consent',
})

# Tiny HTTP server to catch the redirect
auth_code = None
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        nonlocal auth_code
        q = parse_qs(urlparse(self.path).query)
        if 'code' in q:
            auth_code = q['code'][0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<h1>OK!</h1><p>You can close this tab.</p>')
        else:
            self.send_response(400)
            self.end_headers()
    def log_message(self, *a): pass

PORT = 8765
server = HTTPServer(('localhost', PORT), Handler)
print(f'\n=== @lofinippon OAuth flow ===', file=sys.stderr)
print(f'1. Opening browser...', file=sys.stderr)
print(f'2. Sign in with the Google account that owns @lofinippon', file=sys.stderr)
print(f'3. Grant YouTube permissions', file=sys.stderr)
print(f'4. Wait for redirect to localhost:{PORT}', file=sys.stderr)
print(f'\nURL (if browser doesn\'t auto-open): {auth_url}\n', file=sys.stderr)

try:
    webbrowser.open(auth_url)
except: pass

print('Waiting for callback on http://localhost:' + str(PORT) + ' ...', file=sys.stderr)
server.handle_request()

if not auth_code:
    print('ERROR: no auth_code received', file=sys.stderr)
    sys.exit(1)

print(f'\n✓ Got auth code, exchanging for tokens...', file=sys.stderr)

# Exchange code for tokens
token_resp = requests.post('https://oauth2.googleapis.com/token', data={
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'code': auth_code,
    'code_verifier': code_verifier,
    'grant_type': 'authorization_code',
    'redirect_uri': REDIRECT_URI,
})
token_resp.raise_for_status()
tokens = token_resp.json()

print(f'\n=== TOKENS RECEIVED ===', file=sys.stderr)
print(f'  access_token: {tokens.get("access_token", "MISSING")[:40]}...', file=sys.stderr)
print(f'  refresh_token: {tokens.get("refresh_token", "MISSING")[:40]}...', file=sys.stderr)
print(f'  expires_in: {tokens.get("expires_in")}', file=sys.stderr)

# Save to local token file
with open('/workspace/lofinippon-pipeline/token-nippon.json', 'w') as f:
    json.dump({
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': ' '.join(SCOPES),
    }, f, indent=2)

print(f'\n✓ Tokens saved to /workspace/lofinippon-pipeline/token-nippon.json', file=sys.stderr)
print(f'\nNEXT STEP: Update mavis secret YOUTUBE_NIPPON_REFRESH_TOKEN with:', file=sys.stderr)
print(f'  secret update --name=YOUTUBE_NIPPON_REFRESH_TOKEN --value="{tokens["refresh_token"]}"', file=sys.stderr)
print(f'\nRefresh token:', tokens['refresh_token'])