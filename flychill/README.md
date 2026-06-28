# @FlyChill Pipeline

YouTube channel: https://youtube.com/@fly-chill  
Channel ID: `UCvnQnOtZUJ9ZsM1ZgJpvBqQ`

## Architecture

Unlike @The-Lo-Fi and @lofinippon which use direct YouTube Data API, @FlyChill uses **Zernio** for publishing because:
- FlyChill YouTube account was originally connected via Zernio OAuth
- Zernio gives us scheduling + cross-platform for free
- Same OAuth client works for Instagram, TikTok, etc. in future

## Pipeline

1. **Music**: Suno.com tracks (lofi hip hop v5.5)
   - User produces in Suno, shares share URL
   - `download-flychill-tracks.py` downloads via CDN

2. **Visuals**: MiniMax (Image-01)
   - 20 ambient lofi scenes
   - Cool blue/lavender palette, NO mascot (FlyChill has no character)
   - 16:9 1920x1080

3. **Video render**: ffmpeg
   - Loop tracks to ~80 min
   - Cycle through 20 visuals (~4 min each)
   - Audio + video mux → final MP4

4. **Upload**: Zernio API (`upload-flychill-zernio.py`)
   - Presigned URL upload to R2
   - POST to /api/v1/posts with platform: youtube
   - Publishes immediately OR schedules

## First Video (2026-06-28)

- **URL**: https://www.youtube.com/watch?v=8Lxl5-f1TWE
- **Title**: "FlyChill • 1 Hour+ Cozy Lofi Beats to Study Sleep Relax | Rainy Window Vibes"
- **Duration**: 59.3 min
- **Track**: Window Seat Steam (lofi hip hop v5.5) × 27 loops
- **Visuals**: 20 ambient scenes × ~4 min each

## mavis secrets

- `ZERNIO_API_KEY`: Zernio API key
- `FLYCHILL_CHANNEL_ID`: YouTube channel ID
- `FLYCHILL_CHANNEL_HANDLE`: @FlyChill
- `FLYCHILL_ZERNIO_ACCOUNT_ID`: Zernio's account ID for FlyChill YouTube

## OAuth (Zernio)

FlyChill YouTube was connected to Zernio with this OAuth client:
- Project: n8n-quirktag
- Client ID: 444430672231-2nk4kvi0gjhkupfgc5303s3krg90f7pt.apps.googleusercontent.com
- Scopes: youtube.upload, youtube.force-ssl, yt-analytics.readonly, youtube
- Account ID: 6a4076bf9d9472faae0b16dc
