"""
Suno.com API integration client.
Supports both the unofficial API (gcui-art/suno-api) and manual workflow.
"""

import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from config import (
    SUNO_COOKIE, SUNO_EMAIL, SUNO_PASSWORD, TWOCAPTCHA_KEY,
    MUSIC, get_music_raw_path, get_log_path
)


logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TrackInfo:
    """Information about a generated track."""
    track_id: str
    title: str
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    status: str = "pending"
    local_path: Optional[Path] = None


# =============================================================================
# SUNO API CLIENT
# =============================================================================

class SunoClient:
    """
    Client for Suno.com music generation.
    
    Supports two modes:
    1. API mode (requires cookie): Use gcui-art/suno-api for automation
    2. Manual mode: Generate prompts for manual Suno Web UI usage
    
    API Documentation: https://github.com/gcui-art/suno-api
    """

    BASE_URL = "https://api.suno.ai"
    API_URL = "https://studio-api.suno.ai"

    def __init__(
        self,
        cookie: str = SUNO_COOKIE,
        email: str = SUNO_EMAIL,
        password: str = SUNO_PASSWORD,
        two_captcha_key: str = TWOCAPTCHA_KEY,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.cookie = cookie or SUNO_COOKIE
        self.email = email or SUNO_EMAIL
        self.password = password or SUNO_PASSWORD
        self.two_captcha_key = two_captcha_key or TWOCAPTCHA_KEY
        self.config = config or {}
        self.session = requests.Session()
        self._auth_headers: Dict[str, str] = {}

        if self.cookie:
            self._auth_headers = {
                "Cookie": self.cookie,
                "Authorization": f"Bearer {self._extract_bearer_token()}",
            }

    def _extract_bearer_token(self) -> str:
        """Extract bearer token from cookie."""
        # The gcui-art/suno-api uses cookie to get token
        # For now, return empty - the API handles this internally
        return ""

    def _get_api_base(self) -> str:
        """Get API base URL for gcui-art/suno-api."""
        return self.config.get("api_base", "http://localhost:3000")

    # -------------------------------------------------------------------------
    # GENERATION METHODS
    # -------------------------------------------------------------------------

    def generate_track(self, prompt: str, instrumental: bool = True) -> Optional[str]:
        """
        Generate a single track via API.
        
        Args:
            prompt: Music generation prompt
            instrumental: Generate instrumental only (no vocals)
            
        Returns:
            Job ID if successful, None otherwise
        """
        if not self.cookie:
            logger.warning("No Suno cookie - cannot use API mode")
            return None

        try:
            api_base = self._get_api_base()
            response = self.session.post(
                f"{api_base}/api/generate",
                json={
                    "prompt": prompt,
                    "instrumental": instrumental,
                    "make_instrumental": instrumental,
                },
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("generation_id") or data.get("id")
        except Exception as e:
            logger.error(f"Failed to generate track: {e}")
            return None

    def generate_batch(
        self,
        prompts: List[str],
        instrumental: bool = True,
    ) -> List[Optional[str]]:
        """
        Generate multiple tracks in batch.
        
        Args:
            prompts: List of generation prompts
            instrumental: Generate instrumental only
            
        Returns:
            List of job IDs (None for failed generations)
        """
        job_ids = []
        for prompt in prompts:
            job_id = self.generate_track(prompt, instrumental)
            job_ids.append(job_id)
            time.sleep(1)  # Rate limiting
        return job_ids

    def get_generation_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a generation job.
        
        Args:
            job_id: The generation job ID
            
        Returns:
            Status dict with audio_url, video_url, etc. or None
        """
        try:
            api_base = self._get_api_base()
            response = self.session.get(
                f"{api_base}/api/get?ids={job_id}",
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            return data
        except Exception as e:
            logger.error(f"Failed to get generation status: {e}")
            return None

    def poll_until_complete(
        self,
        job_id: str,
        poll_interval: int = 30,
        max_wait_minutes: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """
        Poll a job until completion or timeout.
        
        Args:
            job_id: The generation job ID
            poll_interval: Seconds between polls
            max_wait_minutes: Maximum wait time
            
        Returns:
            Completed generation data or None
        """
        max_attempts = (max_wait_minutes * 60) // poll_interval
        
        for attempt in range(max_attempts):
            status = self.get_generation_status(job_id)
            
            if status:
                status_str = status.get("status", "unknown")
                logger.info(f"Job {job_id}: {status_str} (attempt {attempt + 1}/{max_attempts})")
                
                if status_str == "complete":
                    return status
                elif status_str in ("failed", "error"):
                    logger.error(f"Job {job_id} failed: {status}")
                    return None
            
            time.sleep(poll_interval)
        
        logger.warning(f"Job {job_id} timed out after {max_wait_minutes} minutes")
        return None

    def download_audio(self, url: str, output_path: Path) -> bool:
        """
        Download audio from URL.
        
        Args:
            url: Audio URL
            output_path: Local file path to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download audio: {e}")
            return False

    # -------------------------------------------------------------------------
    # FULL PIPELINE
    # -------------------------------------------------------------------------

    def generate_and_download(
        self,
        prompt: str,
        output_path: Path,
        instrumental: bool = True,
        poll_interval: int = 30,
        max_retries: int = 3,
    ) -> Optional[Path]:
        """
        Complete generation + polling + download workflow.
        
        Args:
            prompt: Music generation prompt
            output_path: Where to save the audio file
            instrumental: Generate instrumental only
            poll_interval: Seconds between status polls
            max_retries: Number of retry attempts
            
        Returns:
            Path to downloaded file or None
        """
        for attempt in range(max_retries):
            logger.info(f"Generation attempt {attempt + 1}/{max_retries}")
            
            # Generate
            job_id = self.generate_track(prompt, instrumental)
            if not job_id:
                logger.error("Failed to start generation")
                continue
            
            # Poll
            result = self.poll_until_complete(job_id, poll_interval)
            if not result:
                logger.error("Generation timed out or failed")
                continue
            
            # Download
            audio_url = result.get("audio_url")
            if audio_url:
                if self.download_audio(audio_url, output_path):
                    return output_path
        
        return None

    def generate_playlist(
        self,
        prompts: List[str],
        output_dir: Path,
        instrumental: bool = True,
        batch_size: int = 5,
    ) -> List[Path]:
        """
        Generate a full playlist of tracks.
        
        Args:
            prompts: List of generation prompts
            output_dir: Directory to save audio files
            instrumental: Generate instrumental only
            batch_size: Number of parallel generation jobs
            
        Returns:
            List of downloaded file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded_files = []
        
        # Process in batches
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: {len(batch)} tracks")
            
            for j, prompt in enumerate(batch):
                track_idx = i + j + 1
                output_path = output_dir / f"track_{track_idx:03d}.mp3"
                
                result = self.generate_and_download(
                    prompt=prompt,
                    output_path=output_path,
                    instrumental=instrumental,
                )
                
                if result:
                    downloaded_files.append(result)
                else:
                    logger.warning(f"Failed to generate track {track_idx}")
        
        return downloaded_files


# =============================================================================
# MANUAL WORKFLOW (No API)
# =============================================================================

class SunoManualWorkflow:
    """
    Manual workflow for when API is not available.
    Generates prompt lists for manual Suno Web UI usage.
    """

    def __init__(self, prompts: List[str], output_dir: Path):
        self.prompts = prompts
        self.output_dir = output_dir

    def generate_prompt_file(self, filename: str = "prompts_manual.txt") -> Path:
        """
        Generate a text file with all prompts for manual use.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to the generated prompt file
        """
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            for i, prompt in enumerate(self.prompts, 1):
                f.write(f"{i}. {prompt}\n")
        
        logger.info(f"Generated prompt file: {output_path}")
        return output_path

    def generate_json_metadata(self, filename: str = "prompts_metadata.json") -> Path:
        """
        Generate JSON file with prompts and metadata.
        
        Args:
            filename: Output filename
            
        Returns:
            Path to the generated JSON file
        """
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "prompts": [
                {
                    "index": i + 1,
                    "prompt": prompt,
                    "expected_duration_minutes": 2.5,
                    "bpm_range": (65, 85),
                }
                for i, prompt in enumerate(self.prompts)
            ],
            "total_tracks": len(self.prompts),
            "estimated_duration_minutes": len(self.prompts) * 2.5,
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Generated metadata file: {output_path}")
        return output_path


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_suno_client() -> SunoClient:
    """Factory function to create SunoClient with config."""
    return SunoClient()


def create_manual_workflow(prompts: List[str]) -> SunoManualWorkflow:
    """Factory function to create manual workflow."""
    from config import MUSIC_RAW_DIR
    return SunoManualWorkflow(prompts, MUSIC_RAW_DIR)


def validate_suno_credentials() -> Dict[str, bool]:
    """
    Validate Suno credentials availability.
    
    Returns:
        Dict with credential status
    """
    return {
        "has_cookie": bool(SUNO_COOKIE),
        "has_email": bool(SUNO_EMAIL),
        "has_password": bool(SUNO_PASSWORD),
        "has_2captcha": bool(TWOCAPTCHA_KEY),
        "can_use_api": bool(SUNO_COOKIE),
    }


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(get_log_path("suno_client")),
            logging.StreamHandler(),
        ],
    )
    
    # Validate credentials
    creds = validate_suno_credentials()
    print(f"Suno credentials: {creds}")
    
    if creds["can_use_api"]:
        print("API mode available")
        client = create_suno_client()
    else:
        print("Manual mode - generate prompt files")
        from config import DEFAULT_MUSIC_PROMPTS
        workflow = create_manual_workflow(DEFAULT_MUSIC_PROMPTS)
        workflow.generate_prompt_file()
        workflow.generate_json_metadata()