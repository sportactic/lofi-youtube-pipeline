# Next Videos Plan (Post v4)

## Track Inventory (2026-06-29 14:00 UTC)
- TheLoFi: 20 v5.5 tracks → 1 more long-form video possible
- LoFiNippon: 10 v5.5 tracks → 1 more long-form video possible
- FlyChill: 10 v5.5 tracks → 1 more long-form video possible

## v5 Timeline (using existing 40 tracks)
- TheLoFi v5: 20 tracks × 2 loops = 80 min, publish ~2026-07-01 22:00 UTC
- LoFiNippon v5: 10 tracks × 3 loops = 45 min, publish ~2026-07-02 04:00 UTC
- FlyChill v5: 10 tracks × 3 loops = 45 min, publish ~2026-07-02 10:00 UTC

## After v5: NEED NEW MUSIC
User must provide full Suno cookie for v6+ batches.
- Need 20+ tracks per channel per day
- 3 channels × 20 = 60 tracks/day

## Generation Plan (when cookie available)
1. TheLoFi: 20 tracks
   - 10 morning themes (rain, vinyl, coffee)
   - 10 evening themes (chameleon, lamp, books)
2. LoFiNippon: 10 tracks
   - 5 zen garden (koto, shamisen)
   - 5 tanuki nights (mischief, lanterns)
3. FlyChill: 10 tracks
   - 5 rain window
   - 5 neon city

## Total per day: 40 tracks
Time per track: ~3 min generation + 1 min download
Daily: 40 × 4 min = ~3 hours of pipeline

## Strategy
- Use SAME prompts as before (already validated quality)
- Use workspace assignment: tracks auto-saved to right channel
- Pre-generate batch of 40 tracks in one session
- Then re-distribute to channels if needed

## Cookie Recovery
When user provides full Suno cookie:
1. Update SUNO_COOKIE env var
2. /workspace/suno-jwt.txt auto-refreshes
3. generate-v2 returns 200 (not 422)
4. New tracks appear in workspace
5. Pipeline continues
