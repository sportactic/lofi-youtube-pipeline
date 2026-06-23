# AGENTS.md — Instructions for AI Agents

This document tells any AI agent (Mavis, MaxHermes, MaxClaw, GPT, Claude, etc.) how to operate the Lofi YouTube pipeline **without asking the user any questions**. Read this file completely before doing anything.

## What this repo is

An automated pipeline that produces a 60+ minute lofi music playlist for the YouTube channel `@The-Lo-Fi`. The pipeline:

1. Generates 15 lofi music tracks via **Suno.com** (unofficial API using `__client` session cookie)
2. Generates background images via **MiniMax Image-01** (16:9)
3. Generates 6- or 10-second video clips via **MiniMax Hailuo 02** (768p)
4. Loops the clips and overlays them with the music
5. Concatenates everything into a single 60-minute MP4 via FFmpeg
6. Uploads the final video to **YouTube** as a public/unlisted video

## Required environment variables

The pipeline reads all credentials from environment variables. **Do not** log or echo them. **Do not** commit them to git. The user is expected to provide them via a secrets manager (mavis `secret`, GitHub Actions secrets, `.env` file, etc.).

| Variable | Description |
|---|---|
| `SUNO_COOKIE` | The `__client` JWT cookie from `https://suno.com` (Application → Cookies) |
| `MINIMAX_API_KEY` | MiniMax API key (`sk-cp-...` format) |
| `YOUTUBE_CLIENT_SECRETS_JSON` | Full JSON content of `client_secrets.json` from Google Cloud Console |
| `YOUTUBE_CHANNEL_HANDLE` | YouTube channel handle (e.g. `@The-Lo-Fi`) — optional, used for metadata |
| `YOUTUBE_CLIENT_SECRETS_FILE` | Path where `YOUTUBE_CLIENT_SECRETS_JSON` should be written. The setup script does this automatically. |
| `YOUTUBE_REFRESH_TOKEN` | Optional. If the OAuth flow has been completed before, this is in the saved `token.json`. Leave empty for first run. |

## First-time setup (run once, takes ~2 minutes)

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Make sure FFmpeg is on PATH
which ffmpeg  # must return a path; install via apt/brew if missing

# 3. Run the YouTube OAuth flow to generate token.json (one-time, requires browser)
python pipeline/main.py --setup-youtube
# This will print a URL. Open it in any browser, grant permission, paste the code back.
# The script will write token.json in the working directory.
```

After step 3, the `token.json` will be persisted on disk. Future runs reuse it.

## Running the full pipeline (production)

```bash
# Make sure all 4 secrets above are exported in your environment.
# Then run:
python pipeline/main.py --full
```

The pipeline writes intermediate files to `pipeline/music/`, `pipeline/visual/`, `pipeline/upload/`. Logs are in `pipeline/logs/`. Each run is resumable — re-running picks up from the last successful stage.

## Running individual stages

```bash
python pipeline/main.py --music         # generate 15 tracks via Suno
python pipeline/main.py --visual        # generate images via MiniMax
python pipeline/main.py --clips         # generate 10-sec video clips via Hailuo 02
python pipeline/main.py --assemble      # FFmpeg concatenate the final 60-min video
python pipeline/main.py --upload        # upload the final video to YouTube
```

## Scheduling (cron)

To run automatically every day at 03:00 in the agent's timezone, the recommended pattern on mavis platform is:

```python
mavis({ command: "cron create", args: {
    agent_name: "me",
    cron_name: "lofi-playlist-daily",
    schedule: "0 3 * * *",
    prompt: """You are running the daily Lofi YouTube playlist job. ... (see mavis memory topic lofi-pipeline-cron-prompt)"""
}})
```

## Where the pipeline reads prompts from

- `pipeline/config/prompts_music.json` — array of 50 lofi prompt seeds (English). The pipeline samples 15 per run.
- `pipeline/config/prompts_visual.json` — visual style seeds (English).
- `pipeline/config/youtube_metadata.json` — video title/description templates.

Edit these files to change the content flavor.

## Cost & runtime estimate

- **Cost per 1-hour playlist**: ~$8-14 USD
  - Suno: ~$2-4 (15 tracks × ~$0.15/track)
  - MiniMax Image-01: ~$2 (90 thumbnails/backgrounds batch)
  - MiniMax Hailuo 02: ~$5-8 (15 clips × 10s × ~$0.03-0.05/s at 768p)
- **Runtime per 1-hour playlist**: 30-90 minutes (music generation is the slowest)
- **YouTube API**: free (under daily quota)

## Failure recovery

The pipeline is idempotent per-stage. If it crashes:
- Re-run with the same env vars. Already-generated music/visuals are reused.
- Delete `pipeline/upload/ready/*.mp4` to force re-upload of the final video.
- Delete `pipeline/logs/main_*.log` to clear stale state.

## What NOT to do

- Do **not** modify `loops_per_clip` away from 24 — the math is `15 tracks × 4 min × 6 loops/section = 60 min` (the documented behavior).
- Do **not** commit `client_secrets.json` or `token.json` — both are in `.gitignore`.
- Do **not** change the `__client` cookie name — Suno's unofficial API looks for that exact key.
- Do **not** call `python main.py --upload` more than once for the same final video — YouTube will reject duplicate uploads.

## Quick smoke test (no real API calls)

```bash
python pipeline/main.py --dry-run
# Validates config, env vars, and pipeline structure without contacting any API.
```
