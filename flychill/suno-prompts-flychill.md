# FlyChill Suno Prompts — Batch 1 (10 themes × 2 variations)

Target: Lofi + Chill + Chillout + Chillhop instrumental tracks, ~2-4 min each
Model: Suno v5.5 (chirp-fenix), instrumental mode (no lyrics)
Style tags: lofi, chillhop, chillout, jazz, ambient

## Generation Strategy
- Each prompt → 2 variations (Suno produces 2 per "Create")
- 10 prompts × 2 = 20 tracks
- Theme-pair splitting: V1 = variation 1 of all 10 themes; V2 = variation 2 of all 10 themes
- ~2-3 loops of 10 tracks → 1-2 hour videos

---

## 1. Midnight Window
**Prompt 1a**: `lofi chillhop instrumental, soft piano chords, jazzy Rhodes, mellow vinyl crackle, slow beat 70bpm, midnight city rain ambience, deep bass, dreamy synth pad, perfect for late night study`

**Prompt 1b**: `chillout ambient lofi, gentle piano melody, soft kick and snare, jazzy upright bass, muted trumpet accents, vinyl hiss texture, 65bpm, window rain ambience, peaceful night mood`

## 2. Moonlit Rooftop
**Prompt 2a**: `lofi chillhop instrumental, dreamy reverb guitar, mellow Rhodes piano, soft brushed drums, vinyl crackle, 75bpm, night rooftop ambient pad, deep sub bass, contemplative mood`

**Prompt 2b**: `chillout lofi beat, warm analog synth pad, slow jazz piano chords, muted trumpet lead, soft kick, 70bpm, distant city noise, rooftop terrace atmosphere, starlit mood`

## 3. Coffee Shop Hours
**Prompt 3a**: `lofi hip hop instrumental, jazzy piano chords, mellow bass guitar, soft snare and kick, vinyl texture, 80bpm, cafe ambience with distant chatter, espresso machine hiss, cozy mood`

**Prompt 3b**: `chillhop lofi beat, warm Rhodes keys, muted jazz guitar, soft boom-bap drums, vinyl crackle, 75bpm, coffee shop background noise, morning light feeling, relaxed vibe`

## 4. Library Pages
**Prompt 4a**: `lofi chillout instrumental, gentle classical guitar, soft piano arpeggios, mellow bass, brushed drums, page turning texture, 72bpm, vintage library ambient, scholarly peaceful mood`

**Prompt 4b**: `chillout ambient lofi, soft harpsichord chords, mellow strings pad, light percussion, vinyl hiss, 68bpm, dusty library atmosphere, contemplative study mood`

## 5. Bedroom Lamp
**Prompt 5a**: `lofi chillhop instrumental, soft electric piano, dreamy synth pad, mellow bass, gentle lofi drums, vinyl crackle, 70bpm, bedroom lamp warmth, late night intimate mood`

**Prompt 5b**: `chillout lofi beat, warm Rhodes piano, soft kick and snare, jazzy bass guitar, muted horn, 73bpm, cozy bedroom atmosphere, sleep-friendly ambient`

## 6. Night Train Cabin
**Prompt 6a**: `lofi chillout instrumental, soft piano melody, mellow synth bass, gentle brushed drums, train rumble texture, 68bpm, night train window view, contemplative travel mood`

**Prompt 6b**: `chillhop ambient beat, warm analog pad, jazzy piano chords, soft percussion, vinyl crackle, 70bpm, train cabin night atmosphere, reflective journey feeling`

## 7. Studio Desk Lamps
**Prompt 7a**: `lofi chillhop instrumental, deep sub bass, soft Rhodes piano, mellow synth chords, slow boom-bap drums, vinyl texture, 78bpm, audio studio ambient, purple lamp mood, focus flow state`

**Prompt 7b**: `chillout lofi beat, warm analog synth pad, soft piano arpeggios, mellow electric bass, brushed snare, 75bpm, late studio session atmosphere, creative zone mood`

## 8. Lakeside Quiet
**Prompt 8a**: `lofi chillout instrumental, soft flute and piano, mellow bass, gentle ambient pads, water ripple texture, 65bpm, lake night atmosphere, peaceful nature mood, stars in sky`

**Prompt 8b**: `ambient chillhop lofi, soft marimba, dreamy synth pad, mellow upright bass, light percussion, 68bpm, calm lakeside reflection, meditation study mood`

## 9. Espresso Pour
**Prompt 9a**: `lofi hip hop instrumental, jazzy electric piano, mellow bass guitar, soft kick and snare, vinyl crackle, 82bpm, morning cafe energy, espresso steam mood, uplifting chill`

**Prompt 9b**: `chillhop lofi beat, warm Rhodes keys, muted jazz guitar, soft boom-bap drums, vinyl texture, 78bpm, coffee ritual atmosphere, productivity mood, golden morning`

## 10. City Lights Dusk
**Prompt 10a**: `lofi chillout instrumental, soft piano melody, mellow synth pad, deep sub bass, brushed drums, 70bpm, city sunset to dusk transition, golden hour turning to blue hour, peaceful urban mood`

**Prompt 10b**: `chillhop ambient lofi, warm analog pad, jazzy piano chords, soft percussion, vinyl hiss, 72bpm, city night lights bokeh, end-of-day contemplation, relaxing urban feel`

---

## Production Notes

### Suno Submission Order
For best variety, generate in batches of 2-3 prompts at a time:
- Batch 1: Prompts 1, 2, 3 (a+b each = 6 generations × 2 = 12 tracks)
- Batch 2: Prompts 4, 5, 6 (12 tracks)
- Batch 3: Prompts 7, 8, 9, 10 (16 tracks)

Total: ~40 generations × 2 variations = ~80 tracks from this prompt set
Each generation costs 5 credits → 200 credits per 40 tracks

### After Production
- Download all variations via CDN (use existing Playwright + API approach)
- Save to `/workspace/flychill-tracks/{theme-name}/variation-1.mp3` etc.
- Categorize by theme keywords in titles

### Expected Track Length
- Suno v5.5 default: ~2:30-4:00 per track
- 10 tracks × ~3min = 30 min raw audio
- 2 loops = 60 min (1 hour) target
- 3 loops = 90 min (1.5 hour) — good for ad-revenue threshold

### Splitting for 2 Videos
Following the pattern from LoFiNippon:
- **Video 1** = variation 1 of all 10 themes (10 tracks × 3 loops = 90 min)
- **Video 2** = variation 2 of all 10 themes (10 tracks × 3 loops = 90 min)

### Title Templates (matching existing FlyChill style)
- "FlyChill • 1 Hour+ of [Theme] Lofi Beats to Study Sleep Relax"
- "Calm Down with the BEST [Theme] Lofi Music for Relaxation"
- "Serene Echoes: A Soothing LoFi Music Collection"

### Description Template
```
Track listing:
1. Midnight Window - Variation 1
2. Moonlit Rooftop - Variation 1
...
[Total: 20 tracks, 90 minutes]

🌙 FlyChill • Lofi • Chill • Chillhop
Perfect for: studying, working, sleeping, relaxing, focus

🔔 Subscribe for daily lo-fi uploads
📧 Business: [email]

© All music produced via Suno AI
```
