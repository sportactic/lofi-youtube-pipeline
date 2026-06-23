# 🎵 Lofi YouTube Pipeline

Automated production pipeline for the YouTube channel **@the-lo-fi**.

Generates a 60+ minute lofi playlist every day — music via Suno.com, visuals via MiniMax, then assembles + uploads the final video to YouTube.

## ✨ What you get

- **15 fresh lofi tracks** per run (4 min each = 60 min total)
- **Backgrounds + 10-sec video clips** per track via Hailuo 02
- **Auto-assembled** into a single MP4 with crossfaded music
- **Auto-uploaded** to YouTube with optimized metadata
- **Runs unattended** — set it and forget it

## 📊 Cost & runtime

| Component | Per 1h playlist |
|---|---|
| Suno (15 tracks) | ~$2-4 |
| MiniMax Image-01 (90 images) | ~$2 |
| MiniMax Hailuo 02 (15×10s clips) | ~$5-8 |
| **Total** | **~$8-14 USD** |
| Runtime | 30-90 minutes |
| YouTube API | free |

## 🚀 Quickstart (for humans)

### 1. Get credentials

You need 4 things:

| Credential | Where to get it |
|---|---|
| `SUNO_COOKIE` | suno.com → log in → F12 → Application → Cookies → `__client` value |
| `MINIMAX_API_KEY` | minimax.io → Settings → API Keys |
| `YOUTUBE_CLIENT_SECRETS_JSON` | Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs → Download JSON |
| `YOUTUBE_CHANNEL_HANDLE` | your YouTube handle (e.g. `@The-Lo-Fi`) |

### 2. Configure

```bash
cp .env.example .env
# edit .env and fill in real values
```

### 3. Setup (one-time, ~2 minutes)

```bash
chmod +x setup.sh
set -a && source .env && set +a
./setup.sh
```

The setup script will:
- Install Python deps
- Materialize `client_secrets.json`
- Walk you through the YouTube OAuth flow (one-time, browser required)

### 4. Run

```bash
# Manual single run
python pipeline/main.py --full

# Or schedule with mavis cron (see AGENTS.md)
```

## 🤖 For AI Agents

**Read `AGENTS.md`** — it contains the full operating manual. The pipeline is designed to run unattended once env vars are set.

## 📁 Project structure

```
.
├── AGENTS.md                # operating manual for AI agents
├── README.md                # this file (human-readable)
├── .env.example             # environment variable template
├── .gitignore
├── setup.sh                 # one-time setup script
└── pipeline/                # the actual pipeline
    ├── main.py              # CLI entry point
    ├── config.py            # env-var-driven config
    ├── suno_client.py       # Suno.com integration
    ├── minimax_client.py    # MiniMax Image-01 + Hailuo 02
    ├── playlist_builder.py  # FFmpeg video assembly
    ├── requirements.txt
    ├── README.md            # pipeline-specific docs
    ├── sample-playlist.md   # example lofi playlist prompts
    └── config/
        ├── prompts_music.json    # 50 lofi prompt seeds
        ├── prompts_visual.json   # visual style seeds
        └── youtube_metadata.json # video title/description templates
```

## 🛠️ CLI reference

```bash
python pipeline/main.py --full              # run everything end-to-end
python pipeline/main.py --music            # stage 1: music generation
python pipeline/main.py --visual           # stage 2: thumbnails + backgrounds
python pipeline/main.py --clips            # stage 3: 10-sec video clips
python pipeline/main.py --assemble         # stage 4: FFmpeg montage
python pipeline/main.py --upload           # stage 5: YouTube upload
python pipeline/main.py --setup-youtube    # one-time OAuth flow
python pipeline/main.py --dry-run          # validate config only
python pipeline/main.py --help
```

## 🐛 Troubleshooting

### "No module named 'requests'"
```bash
pip install -r pipeline/requirements.txt
```

### "ffmpeg not found"
```bash
# Debian/Ubuntu
sudo apt install -y ffmpeg
# macOS
brew install ffmpeg
```

### Suno cookie expired
Re-export `SUNO_COOKIE` from your browser (cookies typically last 1 year for the JWT itself, but the auth.suno.com session may expire sooner). The pipeline will tell you if generation fails with an auth error.

### YouTube upload quota exceeded
YouTube's daily upload quota is generous (default 10,000 units/day, ~6 videos/day at 60min each). If you hit it, the pipeline will surface the error and you can re-run the next day.

### MiniMax API key invalid
The pipeline surfaces MiniMax 401/403 errors clearly. Re-export `MINIMAX_API_KEY` and retry.

## 📜 License

Private use only. Do not redistribute the MiniMax API key or Suno cookie.

## 🤝 Handoff to another agent

If you (human) want to give this to a different AI agent:

1. Push this repo to a GitHub repo (public or private)
2. Tell the new agent: "Clone https://github.com/USER/REPO, read AGENTS.md, set the 4 env vars from your secrets, run `./setup.sh` then `python pipeline/main.py --full`"
3. That's it. The new agent should be able to run the pipeline with zero additional questions.

---

*Built with Mavis + mavis. Pipeline orchestration for the lazy lofi enjoyer.*
