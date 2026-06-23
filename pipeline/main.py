#!/usr/bin/env python3
"""
Lofi YouTube Pipeline - Main Orchestration Script

This script orchestrates the complete pipeline for generating lofi music
videos for YouTube, including:
1. Music generation (Suno.com)
2. Visual assets generation (MiniMax Image-01)
3. Video clips generation (MiniMax Hailuo 02)
4. Audio processing (crossfade, normalize)
5. Video assembly
6. YouTube upload

Usage:
    python main.py --full          # Run complete pipeline
    python main.py --music        # Generate music only
    python main.py --visual       # Generate visuals only
    python main.py --assemble      # Assemble final video
    python main.py --upload       # Upload to YouTube
"""

import os
import sys
import json
import time
import logging
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from config import (
    PIPELINE, MUSIC, VISUAL, VIDEO, YOUTUBE, COSTS,
    MUSIC_RAW_DIR, MUSIC_FINAL_DIR,
    VISUAL_THUMBNAILS_DIR, VISUAL_BACKGROUNDS_DIR, VISUAL_CLIPS_DIR,
    VISUAL_FINAL_DIR, UPLOAD_READY_DIR, LOGS_DIR,
    DEFAULT_MUSIC_PROMPTS, DEFAULT_VISUAL_PROMPTS,
    get_log_path, get_upload_path,
)

from suno_client import SunoClient, SunoManualWorkflow, validate_suno_credentials
from minimax_client import MiniMaxClient, estimate_video_cost, estimate_image_cost
from playlist_builder import PlaylistBuilder, VideoAssembly


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("lofi_pipeline")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # File handler
    log_path = get_log_path("main")
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


logger = setup_logging()


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PipelineState:
    """Tracks the current state of the pipeline."""
    music_generated: bool = False
    thumbnails_generated: bool = False
    backgrounds_generated: bool = False
    video_clips_generated: bool = False
    playlist_built: bool = False
    video_assembled: bool = False
    final_video_ready: bool = False
    youtube_uploaded: bool = False
    
    state_file: Path = Path(".pipeline_state.json")
    
    def save(self):
        """Save state to file."""
        data = {
            "music_generated": self.music_generated,
            "thumbnails_generated": self.thumbnails_generated,
            "backgrounds_generated": self.backgrounds_generated,
            "video_clips_generated": self.video_clips_generated,
            "playlist_built": self.playlist_built,
            "video_assembled": self.video_assembled,
            "final_video_ready": self.final_video_ready,
            "youtube_uploaded": self.youtube_uploaded,
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> bool:
        """Load state from file. Returns True if state exists."""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                data = json.load(f)
            self.music_generated = data.get("music_generated", False)
            self.thumbnails_generated = data.get("thumbnails_generated", False)
            self.backgrounds_generated = data.get("backgrounds_generated", False)
            self.video_clips_generated = data.get("video_clips_generated", False)
            self.playlist_built = data.get("playlist_built", False)
            self.video_assembled = data.get("video_assembled", False)
            self.final_video_ready = data.get("final_video_ready", False)
            self.youtube_uploaded = data.get("youtube_uploaded", False)
            return True
        return False
    
    def reset(self):
        """Reset all state."""
        self.music_generated = False
        self.thumbnails_generated = False
        self.backgrounds_generated = False
        self.video_clips_generated = False
        self.playlist_built = False
        self.video_assembled = False
        self.final_video_ready = False
        self.youtube_uploaded = False


@dataclass
class PipelineResult:
    """Result of a pipeline run."""
    success: bool
    duration_minutes: float
    output_path: Optional[Path] = None
    estimated_cost: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


# =============================================================================
# PIPELINE ORCHESTRATOR
# =============================================================================

class LofiPipeline:
    """
    Main pipeline orchestrator.
    Coordinates all pipeline stages.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.state = PipelineState()
        self.state.load()
        
        # Initialize clients
        self.suno_client = SunoClient()
        self.minimax_client = MiniMaxClient()
        
        # Initialize builders
        self.playlist_builder = PlaylistBuilder()
        self.video_assembly = VideoAssembly()
        
        # Track timing
        self.start_time: Optional[datetime] = None

    # -------------------------------------------------------------------------
    # STAGE 1: MUSIC GENERATION
    # -------------------------------------------------------------------------

    def generate_music(
        self,
        prompts: List[str] = None,
        instrumental: bool = True,
    ) -> bool:
        """
        Generate music tracks using Suno.
        
        Args:
            prompts: List of generation prompts
            instrumental: Generate instrumental only
            
        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("STAGE 1: MUSIC GENERATION")
        logger.info("=" * 60)
        
        if self.state.music_generated:
            logger.info("Music already generated, skipping...")
            return True
        
        prompts = prompts or DEFAULT_MUSIC_PROMPTS
        
        # Check credentials
        creds = validate_suno_credentials()
        
        if not creds["can_use_api"]:
            logger.info("No Suno API credentials - using manual workflow")
            workflow = SunoManualWorkflow(prompts, MUSIC_RAW_DIR)
            workflow.generate_prompt_file()
            workflow.generate_json_metadata()
            
            logger.warning(
                "Manual mode: Please generate tracks in Suno Web UI "
                "and place MP3 files in music/raw/"
            )
            logger.info("Press Enter when complete, or Ctrl+C to abort...")
            input()
            
            # Verify files exist
            tracks = list(MUSIC_RAW_DIR.glob("*.mp3"))
            if len(tracks) >= len(prompts) * 0.8:  # 80% threshold
                self.state.music_generated = True
                self.state.save()
                return True
            else:
                logger.error(f"Insufficient tracks: {len(tracks)} < {len(prompts) * 0.8}")
                return False
        
        # API mode
        logger.info(f"Generating {len(prompts)} tracks...")
        
        try:
            downloaded = self.suno_client.generate_playlist(
                prompts=prompts,
                output_dir=MUSIC_RAW_DIR,
                instrumental=instrumental,
                batch_size=MUSIC.batch_size,
            )
            
            if len(downloaded) >= len(prompts) * 0.8:
                self.state.music_generated = True
                self.state.save()
                logger.info(f"Generated {len(downloaded)} tracks successfully")
                return True
            else:
                logger.error(f"Insufficient tracks: {len(downloaded)}")
                return False
                
        except Exception as e:
            logger.error(f"Music generation failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # STAGE 2: VISUAL ASSETS
    # -------------------------------------------------------------------------

    def generate_visuals(self, prompts: List[str] = None) -> bool:
        """
        Generate thumbnail and background images.
        
        Args:
            prompts: List of image prompts
            
        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("STAGE 2: VISUAL ASSETS GENERATION")
        logger.info("=" * 60)
        
        prompts = prompts or DEFAULT_VISUAL_PROMPTS
        
        # Check quota
        has_quota, msg = self.minimax_client.check_quota(required=10)
        if not has_quota:
            logger.warning(f"MiniMax quota: {msg}")
        
        success = True
        
        # Generate thumbnails
        if not self.state.thumbnails_generated:
            thumbnail_prompts = prompts[:VISUAL.thumbnail["count"]]
            logger.info(f"Generating {len(thumbnail_prompts)} thumbnails...")
            
            try:
                results = self.minimax_client.generate_thumbnails(
                    prompts=thumbnail_prompts,
                    output_dir=VISUAL_THUMBNAILS_DIR,
                )
                
                if results:
                    self.state.thumbnails_generated = True
                    logger.info(f"Generated {len(results)} thumbnails")
                else:
                    success = False
            except Exception as e:
                logger.error(f"Thumbnail generation failed: {e}")
                success = False
        
        # Generate backgrounds
        if not self.state.backgrounds_generated:
            background_prompts = prompts[:VISUAL.background["count"]]
            logger.info(f"Generating {len(background_prompts)} backgrounds...")
            
            try:
                results = self.minimax_client.generate_backgrounds(
                    prompts=background_prompts,
                    output_dir=VISUAL_BACKGROUNDS_DIR,
                )
                
                if results:
                    self.state.backgrounds_generated = True
                    logger.info(f"Generated {len(results)} backgrounds")
                else:
                    success = False
            except Exception as e:
                logger.error(f"Background generation failed: {e}")
                success = False
        
        self.state.save()
        return success

    # -------------------------------------------------------------------------
    # STAGE 3: VIDEO CLIPS
    # -------------------------------------------------------------------------

    def generate_video_clips(
        self,
        prompts: List[str] = None,
        num_clips: int = None,
    ) -> bool:
        """
        Generate video clips using MiniMax Hailuo 02.
        
        Args:
            prompts: List of video prompts
            num_clips: Number of clips to generate
            
        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("STAGE 3: VIDEO CLIPS GENERATION")
        logger.info("=" * 60)
        
        if self.state.video_clips_generated:
            logger.info("Video clips already generated, skipping...")
            return True
        
        prompts = prompts or DEFAULT_VISUAL_PROMPTS
        num_clips = num_clips or VIDEO.unique_clips
        
        # Check quota
        has_quota, msg = self.minimax_client.check_quota(required=num_clips)
        if not has_quota:
            logger.error(f"Insufficient MiniMax quota: {msg}")
            return False
        
        clip_prompts = prompts[:num_clips]
        logger.info(f"Generating {len(clip_prompts)} video clips...")
        
        try:
            results = self.minimax_client.generate_video_clips(
                prompts=clip_prompts,
                output_dir=VISUAL_CLIPS_DIR,
                duration=VIDEO.clip_duration_seconds,
                resolution=VIDEO.resolution,
                model=VIDEO.model,
                parallel_jobs=VIDEO.parallel_jobs,
            )
            
            if len(results) >= num_clips * 0.8:
                self.state.video_clips_generated = True
                self.state.save()
                logger.info(f"Generated {len(results)} video clips")
                return True
            else:
                logger.error(f"Insufficient clips: {len(results)}")
                return False
                
        except Exception as e:
            logger.error(f"Video clip generation failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # STAGE 4: PLAYLIST BUILDING
    # -------------------------------------------------------------------------

    def build_playlist(self, target_minutes: int = None) -> bool:
        """
        Build final music playlist from raw tracks.
        
        Args:
            target_minutes: Target playlist duration
            
        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("STAGE 4: PLAYLIST BUILDING")
        logger.info("=" * 60)
        
        if self.state.playlist_built:
            logger.info("Playlist already built, skipping...")
            return True
        
        target_minutes = target_minutes or PIPELINE.target_duration_minutes
        
        try:
            playlist_path = self.playlist_builder.build_playlist(
                target_minutes=target_minutes,
                output_name="60min_playlist",
            )
            
            if playlist_path and playlist_path.exists():
                self.state.playlist_built = True
                self.state.save()
                logger.info(f"Playlist built: {playlist_path}")
                return True
            else:
                logger.error("Playlist build failed")
                return False
                
        except Exception as e:
            logger.error(f"Playlist building failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # STAGE 5: VIDEO ASSEMBLY
    # -------------------------------------------------------------------------

    def assemble_video(
        self,
        loops_per_clip: int = None,
        target_resolution: str = None,
    ) -> bool:
        """
        Assemble video clips into final montage.
        
        Args:
            loops_per_clip: Number of loops per clip
            target_resolution: Target video resolution
            
        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("STAGE 5: VIDEO ASSEMBLY")
        logger.info("=" * 60)
        
        if self.state.video_assembled:
            logger.info("Video already assembled, skipping...")
            return True
        
        loops_per_clip = loops_per_clip or VIDEO.loops_per_clip
        target_resolution = target_resolution or PIPELINE.target_video_resolution
        
        try:
            video_path = self.video_assembly.assemble_video(
                loops_per_clip=loops_per_clip,
                target_resolution=target_resolution,
                target_fps=PIPELINE.target_video_fps,
            )
            
            if video_path and video_path.exists():
                self.state.video_assembled = True
                self.state.save()
                logger.info(f"Video assembled: {video_path}")
                return True
            else:
                logger.error("Video assembly failed")
                return False
                
        except Exception as e:
            logger.error(f"Video assembly failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # STAGE 6: FINAL COMPOSITION
    # -------------------------------------------------------------------------

    def compose_final_video(self, video_name: str = None) -> Optional[Path]:
        """
        Combine video and audio into final upload-ready file.
        
        Args:
            video_name: Output video name
            
        Returns:
            Path to final video or None
        """
        logger.info("=" * 60)
        logger.info("STAGE 6: FINAL COMPOSITION")
        logger.info("=" * 60)
        
        if self.state.final_video_ready:
            logger.info("Final video already ready, skipping...")
            return get_upload_path("final_video.mp4")
        
        video_name = video_name or "final_video"
        
        # Get video and audio paths
        video_path = VISUAL_FINAL_DIR / "60min_video_only.mp4"
        audio_path = MUSIC_FINAL_DIR / "60min_playlist.mp3"
        
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return None
        
        if not audio_path.exists():
            logger.error(f"Audio not found: {audio_path}")
            return None
        
        output_path = get_upload_path(f"{video_name}.mp4")
        
        try:
            success = self.video_assembly.combine_audio_video(
                video_path=video_path,
                audio_path=audio_path,
                output_path=output_path,
            )
            
            if success:
                self.state.final_video_ready = True
                self.state.save()
                logger.info(f"Final video ready: {output_path}")
                return output_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Final composition failed: {e}")
            return None

    # -------------------------------------------------------------------------
    # YOUTUBE UPLOAD
    # -------------------------------------------------------------------------

    def upload_to_youtube(
        self,
        video_path: Path,
        title: str = None,
        description: str = None,
        tags: List[str] = None,
        thumbnail_path: Path = None,
        playlist_id: str = None,
    ) -> Optional[str]:
        """
        Upload video to YouTube using YouTube Data API v3.
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: Video tags
            thumbnail_path: Path to thumbnail image
            playlist_id: YouTube playlist ID to add video to
            
        Returns:
            Video ID if successful, None otherwise
        """
        logger.info("=" * 60)
        logger.info("STAGE 7: YOUTUBE UPLOAD")
        logger.info("=" * 60)
        
        if self.state.youtube_uploaded:
            logger.info("Already uploaded, skipping...")
            return None
        
        # Default metadata
        title = title or "🌧 Rainy Day Lofi Hip Hop — 1 Hour Study Mix [2026]"
        description = description or """
☕ Relaxing lofi hip hop beats for studying, working & chilling.
Put on headphones and enjoy this 1-hour study session mix. 🎧

#lofi #lofihiphop #studybeats #chillhop #jazzhop #2026
        """.strip()
        tags = tags or [
            "lofi", "lofi hip hop", "study beats", "lofi beats",
            "chillhop", "coffee shop lofi", "rain lofi", "1 hour lofi", "focus music"
        ]
        
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google_auth_oauthlib.flow import InstalledAppFlow
            
            # Check for credentials
            secrets_file = Path(os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json"))
            
            if not secrets_file.exists():
                logger.error(f"YouTube client secrets not found: {secrets_file}")
                logger.info("Please download from: https://console.cloud.google.com")
                return None
            
            # OAuth flow
            SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            credentials = flow.run_local_server(port=0)
            
            youtube = build("youtube", "v3", credentials=credentials)
            
            # Upload video
            request = youtube.videos().insert(
                part="snippet,status,contentDetails",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                        "tags": tags,
                        "categoryId": YOUTUBE.category_id,
                        "defaultLanguage": YOUTUBE.default_language,
                    },
                    "status": {
                        "privacyStatus": YOUTUBE.privacy,
                        "selfDeclaredMadeForKids": YOUTUBE.made_for_kids,
                    },
                },
                media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
            )
            
            response = request.execute()
            video_id = response.get("id")
            
            logger.info(f"Video uploaded: {video_id}")
            
            # Upload thumbnail
            if thumbnail_path and thumbnail_path.exists():
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path)),
                ).execute()
                logger.info("Thumbnail uploaded")
            
            # Add to playlist
            if playlist_id or YOUTUBE.playlist_id:
                pid = playlist_id or YOUTUBE.playlist_id
                youtube.playlistItems().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "playlistId": pid,
                            "resourceId": {
                                "kind": "youtube#video",
                                "videoId": video_id
                            },
                            "position": 0,
                        }
                    }
                ).execute()
                logger.info(f"Added to playlist: {pid}")
            
            self.state.youtube_uploaded = True
            self.state.save()
            
            return video_id
            
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return None

    # -------------------------------------------------------------------------
    # FULL PIPELINE
    # -------------------------------------------------------------------------

    def run_full_pipeline(
        self,
        skip_completed: bool = True,
        upload: bool = False,
    ) -> PipelineResult:
        """
        Run the complete pipeline.
        
        Args:
            skip_completed: Skip stages already completed
            upload: Upload to YouTube after completion
            
        Returns:
            PipelineResult with execution details
        """
        self.start_time = datetime.now()
        errors = []
        
        logger.info("=" * 60)
        logger.info("LOFI YOUTUBE PIPELINE - STARTING")
        logger.info("=" * 60)
        
        # Stage 1: Music
        if not self.generate_music():
            errors.append("Music generation failed")
        
        # Stage 2: Visuals
        if not self.generate_visuals():
            errors.append("Visual generation failed")
        
        # Stage 3: Video clips
        if not self.generate_video_clips():
            errors.append("Video clip generation failed")
        
        # Stage 4: Playlist
        if not self.build_playlist():
            errors.append("Playlist building failed")
        
        # Stage 5: Assembly
        if not self.assemble_video():
            errors.append("Video assembly failed")
        
        # Stage 6: Final composition
        final_video = self.compose_final_video()
        if not final_video:
            errors.append("Final composition failed")
        
        # Stage 7: Upload
        if upload and final_video:
            video_id = self.upload_to_youtube(Path(final_video))
            if not video_id:
                errors.append("YouTube upload failed")
        
        # Calculate duration
        duration = (datetime.now() - self.start_time).total_seconds() / 60
        
        # Estimate cost
        estimated_cost = self._estimate_total_cost()
        
        success = len(errors) == 0
        
        result = PipelineResult(
            success=success,
            duration_minutes=duration,
            output_path=Path(final_video) if final_video else None,
            estimated_cost=estimated_cost,
            errors=errors,
        )
        
        logger.info("=" * 60)
        logger.info(f"PIPELINE {'COMPLETED' if success else 'FAILED'}")
        logger.info(f"Duration: {duration:.1f} minutes")
        logger.info(f"Estimated cost: ${estimated_cost:.2f}")
        if errors:
            logger.error(f"Errors: {errors}")
        logger.info("=" * 60)
        
        return result

    def _estimate_total_cost(self) -> float:
        """Estimate total pipeline cost."""
        # Music (Suno)
        music_cost = MUSIC.tracks_count * COSTS.suno_credit_cost_per_track * 0.003
        
        # Visuals (MiniMax Image-01)
        visual_cost = estimate_image_cost(
            VISUAL.thumbnail["count"] + VISUAL.background["count"]
        )
        
        # Video clips (MiniMax Hailuo 02)
        video_cost = estimate_video_cost(
            VIDEO.unique_clips, VIDEO.model
        )
        
        return music_cost + visual_cost + video_cost

    # -------------------------------------------------------------------------
    # STATUS & UTILITIES
    # -------------------------------------------------------------------------

    def print_status(self):
        """Print current pipeline status."""
        print("\n" + "=" * 60)
        print("PIPELINE STATUS")
        print("=" * 60)
        
        status_items = [
            ("Music Generation", self.state.music_generated),
            ("Thumbnail Generation", self.state.thumbnails_generated),
            ("Background Generation", self.state.backgrounds_generated),
            ("Video Clip Generation", self.state.video_clips_generated),
            ("Playlist Building", self.state.playlist_built),
            ("Video Assembly", self.state.video_assembled),
            ("Final Video Ready", self.state.final_video_ready),
            ("YouTube Upload", self.state.youtube_uploaded),
        ]
        
        for name, status in status_items:
            symbol = "✓" if status else "○"
            print(f"  [{symbol}] {name}")
        
        print("=" * 60 + "\n")

    def reset(self):
        """Reset pipeline state."""
        self.state.reset()
        self.state.save()
        logger.info("Pipeline state reset")

    def setup_youtube_oauth(self):
        """One-time YouTube OAuth flow. Writes token.json in the working directory."""
        from google_auth_oauthlib.flow import InstalledAppFlow
        from pathlib import Path as _P

        secrets_file = _P(os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json"))
        token_file = _P("token.json")

        if not secrets_file.exists():
            print(f"[ERROR] {secrets_file} not found.")
            print("  Set YOUTUBE_CLIENT_SECRETS_FILE or place the JSON in the working directory.")
            return False

        scopes = ["https://www.googleapis.com/auth/youtube.upload",
                  "https://www.googleapis.com/auth/youtube.force-ssl"]

        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_file), scopes)
            creds = flow.run_local_server(port=0)
            token_file.write_text(creds.to_json())
            print(f"[OK] Saved OAuth token to {token_file.resolve()}")
            print("  Future runs of --full or --upload will reuse this token.")
            return True
        except Exception as e:
            print(f"[ERROR] YouTube OAuth failed: {e}")
            return False

    def dry_run_validation(self):
        """Validate that all required env vars and system tools are present."""
        print("=" * 60)
        print("  Lofi YouTube Pipeline - Dry-Run Validation")
        print("=" * 60)
        ok = True

        for var in ("SUNO_COOKIE", "MINIMAX_API_KEY", "YOUTUBE_CLIENT_SECRETS_JSON"):
            val = os.getenv(var, "")
            if not val:
                print(f"  [FAIL] env var missing: {var}")
                ok = False
            else:
                masked = val[:6] + "..." + val[-4:] if len(val) > 12 else "(set)"
                print(f"  [OK]   env var present: {var} = {masked}")

        secrets_file = Path(os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "client_secrets.json"))
        if secrets_file.exists():
            print(f"  [OK]   client_secrets.json present: {secrets_file}")
        else:
            print(f"  [WARN] client_secrets.json not at {secrets_file} (will be needed for upload)")

        import shutil
        if shutil.which("ffmpeg"):
            print(f"  [OK]   ffmpeg on PATH")
        else:
            print(f"  [FAIL] ffmpeg not on PATH - install with apt/brew")
            ok = False

        for mod in ("requests", "googleapiclient", "google.auth", "PIL"):
            try:
                __import__(mod)
                print(f"  [OK]   Python module: {mod}")
            except ImportError:
                print(f"  [WARN] Python module missing: {mod} (run: pip install -r requirements.txt)")

        print("=" * 60)
        print("  Result: " + ("[OK] Ready to run" if ok else "[FAIL] Issues found"))
        print("=" * 60)
        return ok


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Lofi YouTube Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --full           Run complete pipeline
  python main.py --music         Generate music only
  python main.py --visual        Generate visuals only
  python main.py --assemble      Assemble final video only
  python main.py --status        Show pipeline status
  python main.py --reset         Reset pipeline state
        """
    )
    
    parser.add_argument("--full", action="store_true", help="Run complete pipeline")
    parser.add_argument("--music", action="store_true", help="Generate music only")
    parser.add_argument("--visual", action="store_true", help="Generate visuals only")
    parser.add_argument("--clips", action="store_true", help="Generate video clips only")
    parser.add_argument("--playlist", action="store_true", help="Build playlist only")
    parser.add_argument("--assemble", action="store_true", help="Assemble video only")
    parser.add_argument("--compose", action="store_true", help="Compose final video only")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--reset", action="store_true", help="Reset pipeline state")
    parser.add_argument("--no-skip", action="store_true", help="Don't skip completed stages")
    parser.add_argument("--setup-youtube", action="store_true", help="One-time YouTube OAuth flow (writes token.json)")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and env vars only; no API calls")
    
    args = parser.parse_args()
    
    pipeline = LofiPipeline()
    
    # Status
    if args.status:
        pipeline.print_status()
        return
    
    # Reset
    if args.reset:
        pipeline.reset()
        print("Pipeline state reset.")
        return
    
    # YouTube OAuth one-time setup
    if args.setup_youtube:
        pipeline.setup_youtube_oauth()
        return
    
    # Dry run: validate env vars and config only
    if args.dry_run:
        pipeline.dry_run_validation()
        return
    
    # Run stages
    if args.full:
        result = pipeline.run_full_pipeline(
            skip_completed=not args.no_skip,
            upload=args.upload,
        )
        sys.exit(0 if result.success else 1)
    
    elif args.music:
        success = pipeline.generate_music()
        sys.exit(0 if success else 1)
    
    elif args.visual:
        success = pipeline.generate_visuals()
        sys.exit(0 if success else 1)
    
    elif args.clips:
        success = pipeline.generate_video_clips()
        sys.exit(0 if success else 1)
    
    elif args.playlist:
        success = pipeline.build_playlist()
        sys.exit(0 if success else 1)
    
    elif args.assemble:
        success = pipeline.assemble_video()
        sys.exit(0 if success else 1)
    
    elif args.compose:
        result = pipeline.compose_final_video()
        sys.exit(0 if result else 1)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()