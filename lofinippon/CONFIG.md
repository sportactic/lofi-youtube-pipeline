# @lofinippon Pipeline Plan

**Created:** 2026-06-25
**Status:** Awaiting OAuth flow

## Channel
- **Handle:** `@lofinippon`
- **Name:** LoFi Nippon
- **ID:** `UCEXLQ3tlpMu4TWnHojfEP7g`
- **URL:** https://www.youtube.com/@lofinippon
- **Videos:** 15 (1-hour Japanese lo-fi mixes)
- **Style:** Japanese traditional instruments (koto, shamisen, shakuhachi), Tokyo rain, zen garden, cherry blossoms
- **Audience:** Japan lo-fi fans, study/sleep, niche Japanese aesthetic

## Separation Rules (DO NOT MIX)
| Aspect | @The-Lo-Fi | @lofinippon |
|---|---|---|
| Channel ID | `UCpdnbfS3UL-_bKr_8uJGYxQ` | `UCEXLQ3tlpMu4TWnHojfEP7g` |
| Brand | Western cozy + chameleon | Japanese traditional + sakura |
| Instruments | Soft piano, lo-fi beats | Koto, shakuhachi, shamisen |
| Visual style | Anime girl + green chameleon | Anime girl in kimono + torii/zen garden |
| Color palette | Warm amber + teal night | Soft pink sakura + deep indigo + gold leaf |
| Mavis secrets prefix | `YOUTUBE_*` | `YOUTUBE_NIPPON_*` |
| Track directory | `/workspace/the-lofi-tracks/` | `/workspace/lofinippon-tracks/` |
| Visual directory | `/workspace/the-lofi-visuals*/` | `/workspace/lofinippon-visuals/` |
| Video directory | `/workspace/video-production/` | `/workspace/lofinippon-video-production/` |
| GitHub path | `thelofi/` | `lofinippon/` |

## Required Credentials
- ✅ Client JSON received: `/workspace/attachments/e21e0110__33902dd3-6a6a-479e-bbc0-b0e01f6406e3.json`
  - client_id: `<REDACTED — see mavis secret YOUTUBE_NIPPON_CLIENT_SECRETS_JSON>`
  - client_secret: `<REDACTED — see mavis secret YOUTUBE_NIPPON_CLIENT_SECRETS_JSON>`
  - project_id: `gen-lang-client-0785224855`
- ⏳ Need to run OAuth flow to get **refresh token** for @lofinippon channel
  - User must log in with the Google account that owns @lofinippon
  - Resulting refresh token → save as mavis secret `YOUTUBE_NIPPON_REFRESH_TOKEN`
  - Client JSON → save as mavis secret `YOUTUBE_NIPPON_CLIENT_SECRETS_JSON`

## Visual Style Guide (for image_synthesize prompts)

**Primary character:**
- Anime girl in **kimono** (not hoodie/sweater)
- Hair: long black straight, or styled with kanzashi (hairpin flowers)
- Pose: contemplative, sitting in zen garden, on engawa (veranda), under sakura tree
- Setting elements: torii gate, stone lantern, shoji screen, bonsai, koi pond, bamboo grove, pagoda in distance

**Secondary character (mascot):**
- User's existing mascot for this channel — need to check (likely tanuki or fox based on theme)
- If unknown: start with **tanuki** (Japanese raccoon dog, classic lo-fi Nippon mascot)

**Color palette:**
- Soft pink (sakura petals) #FFB7C5
- Deep indigo (night sky) #1a1a3a
- Gold leaf accents #d4af37
- Cream paper-lantern glow #f4e8d0
- Pale jade (bamboo) #7a9e7e

**Common motifs:**
- Falling sakura petals
- Rain on tile roof
- Steam from teacup
- Moonlight through shoji screen
- Distant pagoda silhouette
- Koi swimming in pond

## Suno Prompt Style (v5.5, chirp-fenix)

Each track ~120-190s. Themes:

1. **Sakura Night Walk**: "Dreamy Japanese lo-fi, soft koto arpeggios, gentle shamisen plucks, falling sakura ambience, distant temple bell, 75 BPM, instrumental, no vocals"
2. **Tokyo Train Window**: "Lo-fi hip hop, jazzy piano chords, muted trumpet, train carriage ambience, rain on window, late night city lights, 80 BPM, instrumental, no vocals"
3. **Zen Garden**: "Meditative lo-fi, shakuhachi flute melody, soft koto, bamboo wind chimes, water fountain, peaceful zen atmosphere, 60 BPM, instrumental, no vocals"
4. **Bamboo Forest**: "Atmospheric lo-fi, bamboo wind rustling, distant shakuhachi, soft taiko pulse, mystical forest, 70 BPM, instrumental, no vocals"
5. **Tea Ceremony**: "Soft lo-fi, traditional koto harmonics, gentle shamisen, pouring water ambience, minimalist tea room, 65 BPM, instrumental, no vocals"
6. **Torii Gate Path**: "Melancholic lo-fi, shakuhachi solo, slow koto chords, footsteps on stone path, foggy shrine approach, 70 BPM, instrumental, no vocals"
7. **Old Kyoto Alley**: "Nostalgic lo-fi, jazz piano, soft shamisen, rain on wooden roof, lantern glow, evening alley, 75 BPM, instrumental, no vocals"
8. **Tsukimi Moon**: "Dreamy lo-fi, soft koto, gentle bells, moon-viewing ambience, autumn night, peaceful garden, 60 BPM, instrumental, no vocals"
9. **Sake Bar**: "Warm lo-fi, jazz piano, soft shamisen, sake pouring ambience, late night izakaya, 80 BPM, intimate, instrumental, no vocals"
10. **Mount Fuji Dawn**: "Hopeful lo-fi, koto arpeggios, soft piano, sunrise over Fuji, hopeful new day, 80 BPM, uplifting, instrumental, no vocals"

## Workflow (when active)

1. **Generate tracks** in Suno (user manually, with v5.5)
2. **Download tracks** via Suno API + CDN (same `/me` capture approach)
3. **Generate visuals** with image_synthesize using Japanese-themed prompts
4. **Render video** with Ken Burns motion: `lofinippon-video-production/`
5. **Merge audio** to video, ensure duration match (no cuts)
6. **Upload** to @lofinippon channel via separate credentials
7. **Schedule** for 22:00 UTC (or 11:00 UTC for Japan morning, decide with user)

## GitHub Sync

- Repo: `sportactic/lofi-youtube-pipeline` (existing)
- Path: `lofinippon/` subdirectory
- Files: `lofinippon/CONFIG.md`, `lofinippon/oauth.py`, `lofinippon/upload.py`, `lofinippon/visual-style.md`, `lofinippon/suno-prompts.md`
- TheLoFi and LoFiNippon configs are completely isolated

## Next Steps
1. Save client JSON to mavis secret `YOUTUBE_NIPPON_CLIENT_SECRETS_JSON`
2. Run OAuth flow → get refresh token
3. Test upload (use a 5-min test video first)
4. Generate first set of Japanese tracks (user manual)
5. Generate Japanese visuals
6. Build first 1-hour video
7. Upload to @lofinippon

## OAuth Completion (2026-06-25)
- ✅ OAuth flow completed, refresh token saved to mavis secret `YOUTUBE_NIPPON_REFRESH_TOKEN`
- ✅ Token grants access to UCEXLQ3tlpMu4TWnHojfEP7g (LoFi Nippon) only — not mixed with TheLoFi
- ✅ Token verified: 19 subscribers, 18 existing videos

## 20 New Tracks Produced (2026-06-25)
User produced 20 tracks via Suno (10 themes × 2 variations):
1. Fuji Morning
2. Yoru no Izakaya
3. Moon Garden Drift
4. Lanterns in Kyoto
5. Fog at Torii Path
6. Tea Room Ripples
7. Bamboo Moon Drift
8. Bamboo Water Path
9. Shibuya Raincar
10. Sakura Bell Drift

Total: 3216.3s = 53.6 min
- V1 (variation 1): 1600.2s × 3 loops = 4800.7s = 80.0 min
- V2 (variation 2): 1616.1s × 3 loops = 4848.3s = 80.8 min

## 20 Visuals Generated
10 themes × 2 variations (a/b) each. Kimono girl + tanuki mascot, sakura/indigo/gold palette.

## 2 Videos Planned
- **V1**: `/workspace/lofinippon-video-production/lofinippon-v1-final.mp4` (80.0 min, "a" visuals)
- **V2**: `/workspace/lofinippon-video-production/lofinippon-v2-final.mp4` (80.8 min, "b" visuals)
- Different scheduled publish times via YouTube publishAt

## First Two Videos Uploaded (2026-06-25)
- **V1**: https://www.youtube.com/watch?v=KTAC886oDWg
  - Title: "1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, Zen Garden, Tokyo Rain | Lofi Nippon v1"
  - Publish: 2026-06-26 22:00 UTC (JST 07:00 2026-06-27)
  - Duration: 4800.67s = 80.01 min
  - 10 tracks (Variation A)
  - Visuals: 10x kimono+tanuki scenes (a-variations)
  - Audio match: 0.005s drift
  
- **V2**: https://www.youtube.com/watch?v=mNgeBtWHgtA
  - Title: "1 Hour+ Japanese Lo-Fi Beats to Sleep Study Focus | Sakura, Zen Garden, Tokyo Rain | Lofi Nippon v2"
  - Publish: 2026-06-27 12:00 UTC (JST 21:00 2026-06-27)
  - Duration: 4848.33s = 80.81 min
  - 10 tracks (Variation B)
  - Visuals: 10x kimono+tanuki scenes (b-variations)
  - Audio match: 0.002s drift

- Time between V1 and V2: 14 hours
- Both uploaded to @lofinippon (UCEXLQ3tlpMu4TWnHojfEP7g) using YOUTUBE_NIPPON_* secrets
- NO mix-up with @The-Lo-Fi (UCpdnbfS3UL-_bKr_8uJGYxQ)
