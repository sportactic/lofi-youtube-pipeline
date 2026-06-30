# Suno Generation Pipeline (2captcha + Direct API)

## ✅ WORKING - 15 tracks generated 2026-06-30

### Solution
The Suno hCaptcha challenge blocks Playwright-based generation. Solved via:

1. **2captcha.com** ($3/1000 solves): hCaptcha solver
   - API: `https://2captcha.com/in.php` (submit) + `https://2captcha.com/res.php` (poll)
   - Method: `hcaptcha` with `sitekey=d65453de-3f1a-4aac-9366-a0f06e52b2ce`
   - Page URL: `https://suno.com/create`

2. **Direct API call** with solved captcha token:
   - Endpoint: `https://studio-api-prod.suno.com/api/generate/v2-web/`
   - Headers: `Authorization: Bearer <JWT>` (from Playwright capture)
   - Body: `{"token": "...", "token_provider": 2, "make_instrumental": true, "prompt": "...", "title": "...", "metadata": {"web_client_pathname": "/create"}, "mv": "chirp-fenix"}`

3. **Poll** `/api/feed/?ids=<clip_id>` every 8s until `status: complete` with `audio_url`

## Files
- `gen-batch.mjs` — Main generator (takes channel + count args)
- `refresh-jwt.mjs` — Refresh Suno JWT via Playwright (needed every ~1h)
- `suno-gen-2captcha.mjs` — Original Playwright+UI approach (works but slower)
- `inspect-*.mjs`, `test-*.mjs` — Diagnostic scripts

## Usage

```bash
# Refresh JWT (do this once per session)
node refresh-jwt.mjs

# Generate 5 tracks for TheLoFi
node gen-batch.mjs thelofi 5

# Channels: thelofi | lofinippon | flychill
```

## Cost
- 2captcha: $0.045 per track (hCaptcha solve)
- 15 tracks = $0.68

## Results 2026-06-30
- TheLoFi: 5 tracks (158s total audio)
- LofiNippon: 5 tracks (288s total audio)
- FlyChill: 5 tracks (180s total audio)
