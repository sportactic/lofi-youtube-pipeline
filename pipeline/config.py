"""
Configuration management for Lofi YouTube Pipeline.
All sensitive values are read from environment variables.
"""

import json
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = BASE_DIR / "config"
MUSIC_DIR = BASE_DIR / "music"
MUSIC_RAW_DIR = MUSIC_DIR / "raw"
MUSIC_PROCESSED_DIR = MUSIC_DIR / "processed"
MUSIC_FINAL_DIR = MUSIC_DIR / "final"
VISUAL_DIR = BASE_DIR / "visual"
VISUAL_THUMBNAILS_DIR = VISUAL_DIR / "thumbnails"
VISUAL_BACKGROUNDS_DIR = VISUAL_DIR / "backgrounds"
VISUAL_CLIPS_DIR = VISUAL_DIR / "video_clips"
VISUAL_FINAL_DIR = VISUAL_DIR / "final"
UPLOAD_DIR = BASE_DIR / "upload"
UPLOAD_READY_DIR = UPLOAD_DIR / "ready"
LOGS_DIR = BASE_DIR / "logs"

# Ensure all directories exist
for _dir in [
    CONFIG_DIR, MUSIC_RAW_DIR, MUSIC_PROCESSED_DIR, MUSIC_FINAL_DIR,
    VISUAL_THUMBNAILS_DIR, VISUAL_BACKGROUNDS_DIR, VISUAL_CLIPS_DIR,
    VISUAL_FINAL_DIR, UPLOAD_READY_DIR, LOGS_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)


# =============================================================================
# API KEYS (from environment variables)
# =============================================================================

def _get_env(key: str, default: Optional[str] = None) -> str:
    """Get environment variable with optional default."""
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Required environment variable '{key}' is not set.")
    return value


# Suno.com
SUNO_COOKIE: str = _get_env("SUNO_COOKIE", "")
SUNO_EMAIL: str = _get_env("SUNO_EMAIL", "")
SUNO_PASSWORD: str = _get_env("SUNO_PASSWORD", "")
TWOCAPTCHA_KEY: str = _get_env("TWOCAPTCHA_KEY", "")

# MiniMax
MINIMAX_API_KEY: str = _get_env("MINIMAX_API_KEY", "")
MINIMAX_GROUP_ID: str = _get_env("MINIMAX_GROUP_ID", "")

# YouTube
YOUTUBE_CLIENT_SECRETS_FILE: str = _get_env(
    "YOUTUBE_CLIENT_SECRETS_FILE",
    str(BASE_DIR / "client_secrets.json")
)
YOUTUBE_REFRESH_TOKEN: str = _get_env("YOUTUBE_REFRESH_TOKEN", "")


# =============================================================================
# PIPELINE PARAMETERS
# =============================================================================

@dataclass
class PipelineConfig:
    """Main pipeline configuration."""
    target_duration_minutes: int = 60
    target_video_resolution: str = "1920x1080"
    target_video_fps: int = 25
    video_format: str = "mp4"
    audio_format: str = "aac"
    audio_bitrate: str = "192k"
    audio_normalization_lufs: float = -16.0
    log_level: str = "INFO"
    max_retries: int = 3
    parallel_jobs: int = 5


@dataclass
class MusicConfig:
    """Music generation configuration."""
    provider: str = "suno"
    model: str = "v5.5"
    instrumental_only: bool = True
    tracks_count: int = 50
    bpm_range: tuple = (65, 85)
    crossfade_seconds: float = 3.0
    batch_size: int = 5
    poll_interval_seconds: int = 30
    max_wait_minutes: int = 10


@dataclass
class VisualConfig:
    """Visual assets configuration."""
    thumbnail: dict = field(default_factory=lambda: {
        "resolution": "1920x1080",
        "count": 5,
        "aspect_ratio": "16:9"
    })
    background: dict = field(default_factory=lambda: {
        "resolution": "1920x1080",
        "count": 1,
        "aspect_ratio": "16:9"
    })


@dataclass
class VideoConfig:
    """Video clip generation configuration."""
    provider: str = "minimax"
    model: str = "hailuo-02"
    resolution: str = "768p"
    clip_duration_seconds: int = 10
    unique_clips: int = 15
    loops_per_clip: int = 24  # 15 clips × 10s × 24 loops = 3600s = 60 min
    parallel_jobs: int = 5


@dataclass
class YouTubeConfig:
    """YouTube upload configuration."""
    category_id: str = "10"  # Music
    privacy: str = "public"
    made_for_kids: bool = False
    playlist_id: Optional[str] = None
    default_language: str = "en"


@dataclass
class CostConfig:
    """Cost estimation configuration."""
    suno_credit_cost_per_track: int = 20
    minimax_image_cost_per: float = 0.03
    minimax_video_hailuo02_cost: float = 0.35


# =============================================================================
# INSTANCES
# =============================================================================

PIPELINE = PipelineConfig()
MUSIC = MusicConfig()
VISUAL = VisualConfig()
VIDEO = VideoConfig()
YOUTUBE = YouTubeConfig()
COSTS = CostConfig()


# =============================================================================
# DEFAULT PROMPTS
# =============================================================================

def _load_json_prompts(filename: str) -> list:
    """Load prompts from a JSON config file."""
    try:
        with open(CONFIG_DIR / filename, "r") as f:
            data = json.load(f)
        return data.get("prompts", [])
    except Exception:
        return []


DEFAULT_MUSIC_PROMPTS = _load_json_prompts("prompts_music.json")

if len(DEFAULT_MUSIC_PROMPTS) < 10:
    # Fallback if JSON is missing or empty
    DEFAULT_MUSIC_PROMPTS = [
        "Lo-fi hip hop, 75 BPM, dusty drums, jazzy piano, vinyl crackle, study vibe",
        "Chill lofi, 70 BPM, soft guitar, warm bass, lo-fi aesthetic, rainy day",
        "Lo-fi beats, 80 BPM, mellow sax, calm drums, coffee shop mood",
        "Lofi hip hop, 65 BPM, mellow keys, slow drums, night study",
        "Relaxing lofi, 72 BPM, soft pad, steady beat, cozy atmosphere",
        "Chillhop, 78 BPM, piano melody, dust vinyl, focus music",
        "Lo-fi jazz hop, 68 BPM, upright bass, light snare, relax",
        "Study beats, 85 BPM, bright keys, gentle drums, concentration",
        "Lofi ambient, 70 BPM, warm synth, slow rhythm, rain sounds",
        "Mellow lofi, 75 BPM, Rhodes piano, soft kicks, evening chill",
    ]

DEFAULT_VISUAL_PROMPTS = [
    "Rainy window view, soft golden light, cozy cafe interior, lo-fi aesthetic",
    "Old record player, vinyl spinning, warm amber lighting, vintage aesthetic",
    "Coffee cup with steam, wooden table, rain outside window, cozy mood",
    "City night skyline, neon lights reflection, rainy streets, lo-fi vibe",
    "Books stacked on desk, warm lamp light, peaceful study corner",
    "Headphones on vintage speaker, soft glow, lo-fi album aesthetic",
    "Mountain landscape at sunset, warm colors, peaceful vibes, lofi art",
    "Cat sleeping on keyboard, cozy workspace, warm tones",
    "Vinyl collection shelf, warm lighting, nostalgic feeling",
    "Rainy street with lamp posts, reflections on wet ground, cozy night",
    "Hot chocolate with marshmallows, soft blanket, rainy day mood",
    "Vintage radio on windowsill, plants around, golden hour light",
    "Street musician with guitar, warm evening light, lo-fi aesthetic",
    "Beach at sunset, calm waves, nostalgic lo-fi art style",
    "Forest path in morning mist, soft sunlight, peaceful nature",
]


# =============================================================================
# HELPERS
# =============================================================================

def get_log_path(name: str) -> Path:
    """Get log file path for a given module name."""
    return LOGS_DIR / f"{name}.log"


def get_music_raw_path(track_name: str) -> Path:
    """Get raw music file path."""
    return MUSIC_RAW_DIR / track_name


def get_music_final_path(filename: str) -> Path:
    """Get final music file path."""
    return MUSIC_FINAL_DIR / filename


def get_visual_thumbnail_path(index: int) -> Path:
    """Get thumbnail path by index."""
    return VISUAL_THUMBNAILS_DIR / f"thumbnail_{index:03d}.png"


def get_visual_clip_path(index: int) -> Path:
    """Get video clip path by index."""
    return VISUAL_CLIPS_DIR / f"clip_{index:03d}.mp4"


def get_final_video_path(name: str) -> Path:
    """Get final video output path."""
    return VISUAL_FINAL_DIR / f"{name}.mp4"


def get_upload_path(filename: str) -> Path:
    """Get upload-ready file path."""
    return UPLOAD_READY_DIR / filename