#!/usr/bin/env bash
# setup.sh — One-shot setup for a brand-new agent.
# Idempotent: safe to re-run.

set -euo pipefail

# ----- 1. Pre-flight: check required env vars -----------------------------
required=(
  SUNO_COOKIE
  MINIMAX_API_KEY
  YOUTUBE_CLIENT_SECRETS_JSON
)
for var in "${required[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "❌ Missing required env var: $var" >&2
    echo "   Source your .env file first:  set -a && source .env && set +a" >&2
    exit 1
  fi
done
echo "✅ Required env vars present"

# ----- 2. Check FFmpeg -----------------------------------------------------
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "❌ ffmpeg not found. Install with:" >&2
  echo "   Debian/Ubuntu:  sudo apt install -y ffmpeg" >&2
  echo "   macOS:          brew install ffmpeg" >&2
  exit 1
fi
FFMPEG_VERSION=$(ffmpeg -version | head -n1 | awk '{print $3}')
echo "✅ ffmpeg $FFMPEG_VERSION found"

# ----- 3. Check Python + pip -----------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 not found" >&2
  exit 1
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PY_VERSION found"

# ----- 4. Install Python dependencies -------------------------------------
echo "📦 Installing Python dependencies..."
pip install -q -r pipeline/requirements.txt

# ----- 5. Materialize YouTube client_secrets.json --------------------------
if [ -n "${YOUTUBE_CLIENT_SECRETS_FILE:-}" ]; then
  printf '%s' "$YOUTUBE_CLIENT_SECRETS_JSON" > "$YOUTUBE_CLIENT_SECRETS_FILE"
  echo "✅ Wrote YouTube client_secrets.json to $YOUTUBE_CLIENT_SECRETS_FILE"
fi

# ----- 6. Create runtime directories --------------------------------------
mkdir -p pipeline/{config,music/{raw,processed,final},visual/{thumbnails,backgrounds,video_clips,final},upload/ready,logs}

# ----- 7. YouTube OAuth (only first time) --------------------------------
if [ ! -f token.json ]; then
  echo "🔑 First-time YouTube OAuth setup required."
  echo "   Running: python3 pipeline/main.py --setup-youtube"
  echo "   Follow the printed URL, grant permission, paste the code back."
  python3 pipeline/main.py --setup-youtube
else
  echo "✅ YouTube token.json already exists, skipping OAuth setup"
fi

echo ""
echo "🎉 Setup complete! Run the pipeline with:"
echo "   python3 pipeline/main.py --full"
