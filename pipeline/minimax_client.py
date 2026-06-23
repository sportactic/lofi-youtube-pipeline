"""
MiniMax API integration client for image and video generation.
Handles Image-01 for thumbnails/backgrounds and Hailuo 02 for video clips.
"""

import time
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode

import requests

from config import (
    MINIMAX_API_KEY, MINIMAX_GROUP_ID, VIDEO,
    VISUAL_THUMBNAILS_DIR, VISUAL_BACKGROUNDS_DIR, VISUAL_CLIPS_DIR,
    get_log_path
)


logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ImageResult:
    """Result from image generation."""
    image_id: str
    image_url: str
    local_path: Optional[Path] = None


@dataclass
class VideoResult:
    """Result from video generation."""
    video_id: str
    video_url: str
    local_path: Optional[Path] = None


@dataclass
class GenerationStatus:
    """Generation job status."""
    task_id: str
    status: str  # "pending", "processing", "success", "failed"
    progress: float = 0.0
    result_url: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# MINIMAX API CLIENT
# =============================================================================

class MiniMaxClient:
    """
    Client for MiniMax API (Image-01 and Hailuo 02).
    
    API Documentation: https://www.minimaxi.com/document
    """

    BASE_URL = "https://api.minimax.io"
    API_VERSION = "v1"
    
    # Endpoints
    IMAGE_ENDPOINT = "/text2image/image generation"
    VIDEO_ENDPOINT = "/text2video/video_generation"
    ACCOUNT_INFO_ENDPOINT = "/account/info"
    TASK_STATUS_ENDPOINT = "/task/get"

    def __init__(
        self,
        api_key: str = MINIMAX_API_KEY,
        group_id: str = MINIMAX_GROUP_ID,
    ):
        self.api_key = api_key or MINIMAX_API_KEY
        self.group_id = group_id or MINIMAX_GROUP_ID
        self.session = requests.Session()
        self._auth_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # -------------------------------------------------------------------------
    # ACCOUNT
    # -------------------------------------------------------------------------

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information and quota."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/api{self.ACCOUNT_INFO_ENDPOINT}",
                headers=self._auth_headers,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return {"error": str(e)}

    def check_quota(self, required: int = 10) -> Tuple[bool, str]:
        """
        Check if sufficient quota is available.
        
        Args:
            required: Minimum required quota
            
        Returns:
            (has_quota, message)
        """
        info = self.get_account_info()
        
        if "error" in info:
            return False, info["error"]
        
        # Response format may vary - adjust based on actual API
        credits = info.get("data", {}).get("credits", info.get("credits", 0))
        
        if credits < required:
            return False, f"Insufficient quota: {credits} < {required}"
        
        return True, f"Quota available: {credits}"

    # -------------------------------------------------------------------------
    # IMAGE GENERATION (Image-01)
    # -------------------------------------------------------------------------

    def generate_images(
        self,
        prompts: List[str],
        resolution: str = "1920x1080",
        aspect_ratio: str = "16:9",
        num_images: int = 1,
    ) -> List[ImageResult]:
        """
        Generate images using Image-01.
        
        Args:
            prompts: List of generation prompts
            resolution: Image resolution (e.g., "1920x1080")
            aspect_ratio: Aspect ratio (e.g., "16:9", "1:1")
            num_images: Number of images per prompt
            
        Returns:
            List of ImageResult objects
        """
        results = []
        
        for i, prompt in enumerate(prompts):
            try:
                payload = {
                    "model": "Image-01",
                    "prompt": prompt,
                    "num_images": num_images,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                }
                
                response = self.session.post(
                    f"{self.BASE_URL}/api{self.IMAGE_ENDPOINT}",
                    headers=self._auth_headers,
                    json=payload,
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse response - format may vary
                image_urls = data.get("data", {}).get("images", [])
                
                for j, url in enumerate(image_urls):
                    results.append(ImageResult(
                        image_id=f"img_{i:03d}_{j:03d}",
                        image_url=url,
                    ))
                
                logger.info(f"Generated {len(image_urls)} images for prompt {i + 1}")
                
            except Exception as e:
                logger.error(f"Failed to generate image for prompt {i + 1}: {e}")
        
        return results

    def generate_thumbnails(
        self,
        prompts: List[str],
        output_dir: Path = VISUAL_THUMBNAILS_DIR,
    ) -> List[ImageResult]:
        """
        Generate thumbnail images.
        
        Args:
            prompts: List of thumbnail prompts
            output_dir: Directory to save images
            
        Returns:
            List of ImageResult with local paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = self.generate_images(
            prompts=prompts,
            resolution="1920x1080",
            aspect_ratio="16:9",
        )
        
        # Download images
        for result in results:
            local_path = output_dir / f"{result.image_id}.png"
            if self._download_file(result.image_url, local_path):
                result.local_path = local_path
        
        return results

    def generate_backgrounds(
        self,
        prompts: List[str],
        output_dir: Path = VISUAL_BACKGROUNDS_DIR,
    ) -> List[ImageResult]:
        """
        Generate background images.
        
        Args:
            prompts: List of background prompts
            output_dir: Directory to save images
            
        Returns:
            List of ImageResult with local paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = self.generate_images(
            prompts=prompts,
            resolution="1920x1080",
            aspect_ratio="16:9",
        )
        
        # Download images
        for result in results:
            local_path = output_dir / f"{result.image_id}.png"
            if self._download_file(result.image_url, local_path):
                result.local_path = local_path
        
        return results

    # -------------------------------------------------------------------------
    # VIDEO GENERATION (Hailuo 02)
    # -------------------------------------------------------------------------

    def generate_video(
        self,
        prompt: str,
        duration: int = 10,
        resolution: str = "768p",
        model: str = "hailuo-02",
    ) -> Optional[str]:
        """
        Generate a single video clip.
        
        Args:
            prompt: Video generation prompt
            duration: Video duration in seconds (10 or 15)
            resolution: Video resolution ("768p" or "1080p")
            model: Video model ("hailuo-02" or "hailuo-01")
            
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "duration": duration,
                "resolution": resolution,
            }
            
            response = self.session.post(
                f"{self.BASE_URL}/api{self.VIDEO_ENDPOINT}",
                headers=self._auth_headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract task ID from response
            task_id = data.get("data", {}).get("task_id") or data.get("task_id")
            logger.info(f"Started video generation: {task_id}")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to generate video: {e}")
            return None

    def get_video_status(self, task_id: str) -> GenerationStatus:
        """
        Get video generation status.
        
        Args:
            task_id: The generation task ID
            
        Returns:
            GenerationStatus object
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/api{self.TASK_STATUS_ENDPOINT}",
                headers=self._auth_headers,
                params={"task_id": task_id},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            
            status_data = data.get("data", data)
            
            return GenerationStatus(
                task_id=task_id,
                status=status_data.get("status", "unknown"),
                progress=status_data.get("progress", 0.0),
                result_url=status_data.get("video_url") or status_data.get("url"),
                error=status_data.get("error"),
            )
            
        except Exception as e:
            logger.error(f"Failed to get video status: {e}")
            return GenerationStatus(task_id=task_id, status="error", error=str(e))

    def poll_video_until_complete(
        self,
        task_id: str,
        poll_interval: int = 30,
        max_wait_minutes: int = 15,
    ) -> Optional[str]:
        """
        Poll video task until completion.
        
        Args:
            task_id: The generation task ID
            poll_interval: Seconds between polls
            max_wait_minutes: Maximum wait time
            
        Returns:
            Video URL if successful, None otherwise
        """
        max_attempts = (max_wait_minutes * 60) // poll_interval
        
        for attempt in range(max_attempts):
            status = self.get_video_status(task_id)
            
            logger.info(
                f"Video {task_id}: {status.status} "
                f"(progress: {status.progress:.0%}) "
                f"[{attempt + 1}/{max_attempts}]"
            )
            
            if status.status == "success":
                return status.result_url
            elif status.status in ("failed", "error"):
                logger.error(f"Video generation failed: {status.error}")
                return None
            
            time.sleep(poll_interval)
        
        logger.warning(f"Video task {task_id} timed out")
        return None

    def download_video(self, url: str, output_path: Path) -> bool:
        """
        Download video from URL.
        
        Args:
            url: Video URL
            output_path: Local file path
            
        Returns:
            True if successful, False otherwise
        """
        return self._download_file(url, output_path)

    def _download_file(self, url: str, output_path: Path) -> bool:
        """Download file from URL to local path."""
        try:
            response = self.session.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download: {e}")
            return False

    # -------------------------------------------------------------------------
    # BATCH VIDEO GENERATION
    # -------------------------------------------------------------------------

    def generate_video_clips(
        self,
        prompts: List[str],
        output_dir: Path = VISUAL_CLIPS_DIR,
        duration: int = 10,
        resolution: str = "768p",
        model: str = "hailuo-02",
        parallel_jobs: int = 5,
        max_retries: int = 3,
    ) -> List[VideoResult]:
        """
        Generate multiple video clips in parallel.
        
        Args:
            prompts: List of video prompts
            output_dir: Directory to save videos
            duration: Video duration in seconds
            resolution: Video resolution
            model: Video model
            parallel_jobs: Number of parallel jobs
            max_retries: Retry attempts per clip
            
        Returns:
            List of VideoResult objects with local paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check quota first
        has_quota, msg = self.check_quota(required=len(prompts))
        if not has_quota:
            logger.warning(f"Quota check: {msg}")
        
        results: List[VideoResult] = []
        task_map: Dict[str, Tuple[int, Path]] = {}  # task_id -> (index, path)
        
        # Start all generation tasks
        logger.info(f"Starting {len(prompts)} video generation tasks...")
        
        for i, prompt in enumerate(prompts):
            output_path = output_dir / f"clip_{i + 1:03d}.mp4"
            
            for attempt in range(max_retries):
                task_id = self.generate_video(
                    prompt=prompt,
                    duration=duration,
                    resolution=resolution,
                    model=model,
                )
                
                if task_id:
                    task_map[task_id] = (i, output_path)
                    break
                
                logger.warning(f"Failed to start clip {i + 1}, attempt {attempt + 1}")
                time.sleep(5)
        
        # Poll all tasks
        logger.info(f"Polling {len(task_map)} tasks for completion...")
        
        completed = set()
        while len(completed) < len(task_map):
            for task_id in list(task_map.keys()):
                if task_id in completed:
                    continue
                
                status = self.get_video_status(task_id)
                
                if status.status == "success" and status.result_url:
                    index, output_path = task_map[task_id]
                    
                    if self.download_video(status.result_url, output_path):
                        results.append(VideoResult(
                            video_id=task_id,
                            video_url=status.result_url,
                            local_path=output_path,
                        ))
                    
                    completed.add(task_id)
                    logger.info(f"Completed: {task_id} ({len(completed)}/{len(task_map)})")
                    
                elif status.status in ("failed", "error"):
                    logger.error(f"Video {task_id} failed: {status.error}")
                    completed.add(task_id)
            
            if len(completed) < len(task_map):
                time.sleep(30)
        
        return results


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_minimax_client() -> MiniMaxClient:
    """Factory function to create MiniMaxClient."""
    return MiniMaxClient()


def estimate_video_cost(num_clips: int, model: str = "hailuo-02") -> float:
    """
    Estimate cost for video generation.
    
    Args:
        num_clips: Number of clips
        model: Video model
        
    Returns:
        Estimated cost in USD
    """
    cost_per_clip = {
        "hailuo-02": 0.35,
        "hailuo-01": 0.50,
    }
    return num_clips * cost_per_clip.get(model, 0.35)


def estimate_image_cost(num_images: int) -> float:
    """
    Estimate cost for image generation.
    
    Args:
        num_images: Number of images
        
    Returns:
        Estimated cost in USD
    """
    return num_images * 0.03  # ~$0.03 per Image-01


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(get_log_path("minimax_client")),
            logging.StreamHandler(),
        ],
    )
    
    client = create_minimax_client()
    
    # Check quota
    has_quota, msg = client.check_quota()
    print(f"Quota check: {msg}")
    
    # Test image generation (if quota available)
    if has_quota and len(sys.argv) > 1 and sys.argv[1] == "test-image":
        from config import DEFAULT_VISUAL_PROMPTS
        
        results = client.generate_thumbnails(
            prompts=DEFAULT_VISUAL_PROMPTS[:3],
        )
        print(f"Generated {len(results)} thumbnails")
    
    # Test video generation
    elif len(sys.argv) > 1 and sys.argv[1] == "test-video":
        from config import DEFAULT_VISUAL_PROMPTS
        
        task_id = client.generate_video(
            prompt=DEFAULT_VISUAL_PROMPTS[0],
            duration=10,
        )
        print(f"Started video task: {task_id}")