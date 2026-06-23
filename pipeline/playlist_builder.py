"""
Playlist builder for combining and processing music tracks.
Handles track ordering, crossfade, normalization, and final assembly.
"""

import os
import re
import json
import logging
import subprocess
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from config import (
    MUSIC_RAW_DIR, MUSIC_PROCESSED_DIR, MUSIC_FINAL_DIR,
    VISUAL_CLIPS_DIR, VISUAL_FINAL_DIR, UPLOAD_READY_DIR,
    MUSIC, PIPELINE, get_log_path
)


logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Track:
    """Represents a music track."""
    path: Path
    filename: str
    duration_seconds: float = 0.0
    bpm: Optional[int] = None
    key: Optional[str] = None
    
    @property
    def name(self) -> str:
        return self.path.stem


@dataclass
class PlaylistSection:
    """A section of the playlist with BPM range."""
    name: str
    start_minute: int
    end_minute: int
    bpm_range: Tuple[int, int]
    track_count: int = 0


# =============================================================================
# TRACK UTILITIES
# =============================================================================

def get_track_duration(file_path: Path) -> float:
    """
    Get audio file duration using ffprobe.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(file_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        logger.warning(f"Failed to get duration for {file_path}: {e}")
        return 0.0


def analyze_track(file_path: Path) -> Dict[str, any]:
    """
    Analyze track properties using ffprobe.
    
    Args:
        file_path: Path to audio file
        
    Returns:
        Dict with track properties
    """
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_name,sample_rate,channels,bit_rate",
            "-show_entries", "format=duration,size,bit_rate",
            "-of", "json",
            str(file_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        
        format_info = data.get("format", {})
        streams = data.get("streams", [{}])
        audio_stream = streams[0] if streams else {}
        
        return {
            "duration": float(format_info.get("duration", 0)),
            "size_bytes": int(format_info.get("size", 0)),
            "bitrate": int(format_info.get("bit_rate", 0)),
            "codec": audio_stream.get("codec_name", "unknown"),
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": int(audio_stream.get("channels", 0)),
        }
    except Exception as e:
        logger.error(f"Failed to analyze track {file_path}: {e}")
        return {}


def sort_tracks_by_bpm(tracks: List[Track]) -> List[Track]:
    """
    Sort tracks by BPM for smooth transitions.
    
    Args:
        tracks: List of Track objects
        
    Returns:
        Sorted list of tracks
    """
    # Group by BPM ranges
    bpm_groups = {
        "slow": [],    # 65-72 BPM
        "medium": [],  # 73-80 BPM
        "fast": [],    # 81-90 BPM
    }
    
    for track in tracks:
        if track.bpm:
            if track.bpm <= 72:
                bpm_groups["slow"].append(track)
            elif track.bpm <= 80:
                bpm_groups["medium"].append(track)
            else:
                bpm_groups["fast"].append(track)
        else:
            bpm_groups["medium"].append(track)
    
    # Interleave groups for variety
    sorted_tracks = []
    for group in [bpm_groups["slow"], bpm_groups["medium"], bpm_groups["fast"]]:
        sorted_tracks.extend(sorted(group, key=lambda t: t.bpm or 75))
    
    return sorted_tracks


# =============================================================================
# PLAYLIST BUILDER
# =============================================================================

class PlaylistBuilder:
    """
    Build and process lofi music playlists.
    
    Handles:
    - Track ordering by BPM for smooth transitions
    - Crossfade application
    - Audio normalization (LUFS)
    - Section-based arrangement
    """

    def __init__(
        self,
        raw_dir: Path = MUSIC_RAW_DIR,
        processed_dir: Path = MUSIC_PROCESSED_DIR,
        final_dir: Path = MUSIC_FINAL_DIR,
        config: Optional[Dict] = None,
    ):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.final_dir = Path(final_dir)
        self.config = config or {}
        
        # Ensure directories exist
        for _dir in [self.processed_dir, self.final_dir]:
            _dir.mkdir(parents=True, exist_ok=True)

    def scan_raw_tracks(self) -> List[Track]:
        """
        Scan raw directory for audio files.
        
        Returns:
            List of Track objects
        """
        tracks = []
        audio_extensions = {".mp3", ".wav", ".flac", ".m4a", ".ogg"}
        
        for file_path in sorted(self.raw_dir.glob("*")):
            if file_path.suffix.lower() in audio_extensions:
                track = Track(
                    path=file_path,
                    filename=file_path.name,
                    duration_seconds=get_track_duration(file_path),
                )
                tracks.append(track)
        
        logger.info(f"Found {len(tracks)} raw tracks")
        return tracks

    def create_section_order(self, target_minutes: int = 60) -> List[PlaylistSection]:
        """
        Create playlist sections based on target duration.
        
        Args:
            target_minutes: Target playlist duration
            
        Returns:
            List of PlaylistSection objects
        """
        sections = [
            PlaylistSection(
                name="opening",
                start_minute=0,
                end_minute=5,
                bpm_range=(65, 72),
            ),
            PlaylistSection(
                name="body_calm",
                start_minute=5,
                end_minute=25,
                bpm_range=(70, 78),
            ),
            PlaylistSection(
                name="body_energetic",
                start_minute=25,
                end_minute=45,
                bpm_range=(75, 82),
            ),
            PlaylistSection(
                name="cooldown",
                start_minute=45,
                end_minute=55,
                bpm_range=(72, 78),
            ),
            PlaylistSection(
                name="closing",
                start_minute=55,
                end_minute=target_minutes,
                bpm_range=(65, 72),
            ),
        ]
        
        return sections

    def apply_crossfade(
        self,
        input_files: List[Path],
        output_path: Path,
        crossfade_seconds: float = 3.0,
    ) -> bool:
        """
        Concatenate audio files with crossfade.
        
        Args:
            input_files: List of input audio files
            output_path: Output file path
            crossfade_seconds: Crossfade duration
            
        Returns:
            True if successful
        """
        if not input_files:
            logger.error("No input files provided")
            return False
        
        if len(input_files) == 1:
            # Single file - just copy
            import shutil
            shutil.copy(input_files[0], output_path)
            return True
        
        try:
            # Create concat file
            concat_file = self.processed_dir / "concat_list.txt"
            with open(concat_file, "w") as f:
                for file_path in input_files:
                    f.write(f"file '{file_path}'\n")
            
            # Build FFmpeg command
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-filter_complex",
                f"acrossfade=d={crossfade_seconds}:c1=tri:c2=tri",
                "-ar", "44100",
                "-ac", "2",
                str(output_path),
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error(f"Crossfade failed: {result.stderr}")
                return False
            
            logger.info(f"Applied crossfade: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Crossfade error: {e}")
            return False

    def normalize_audio(
        self,
        input_path: Path,
        output_path: Path,
        target_lufs: float = -16.0,
        target_tp: float = -1.5,
        loudness_range: float = 11.0,
    ) -> bool:
        """
        Normalize audio to target LUFS.
        
        Args:
            input_path: Input audio file
            output_path: Output file path
            target_lufs: Target integrated loudness
            target_tp: Target true peak
            loudness_range: Target loudness range
            
        Returns:
            True if successful
        """
        try:
            # Two-pass loudness normalization
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-af",
                f"loudnorm=I={target_lufs}:TP={target_tp}:LRA={loudness_range}",
                "-ar", "44100",
                "-ac", "2",
                str(output_path),
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                logger.error(f"Normalize failed: {result.stderr}")
                return False
            
            logger.info(f"Normalized audio: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Normalize error: {e}")
            return False

    def trim_to_duration(
        self,
        input_path: Path,
        output_path: Path,
        target_seconds: float,
    ) -> bool:
        """
        Trim audio to exact duration.
        
        Args:
            input_path: Input audio file
            output_path: Output file path
            target_seconds: Target duration in seconds
            
        Returns:
            True if successful
        """
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(input_path),
                "-t", str(target_seconds),
                "-c", "copy",
                str(output_path),
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"Trim failed: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Trim error: {e}")
            return False

    def build_playlist(
        self,
        target_minutes: int = 60,
        output_name: str = "60min_playlist",
    ) -> Optional[Path]:
        """
        Build complete playlist from raw tracks.
        
        Args:
            target_minutes: Target duration
            output_name: Output filename (without extension)
            
        Returns:
            Path to final playlist file or None
        """
        logger.info(f"Building playlist: {target_minutes} minutes")
        
        # Scan tracks
        tracks = self.scan_raw_tracks()
        if not tracks:
            logger.error("No raw tracks found")
            return None
        
        # Sort by BPM
        sorted_tracks = sort_tracks_by_bpm(tracks)
        
        # Calculate total duration
        total_duration = sum(t.duration_seconds for t in sorted_tracks)
        target_seconds = target_minutes * 60
        
        logger.info(f"Total track duration: {total_duration / 60:.1f} minutes")
        
        # Select tracks to fit target duration
        selected_tracks = []
        current_duration = 0
        
        for track in sorted_tracks:
            if current_duration + track.duration_seconds <= target_seconds + 60:
                selected_tracks.append(track)
                current_duration += track.duration_seconds
            if current_duration >= target_seconds:
                break
        
        logger.info(f"Selected {len(selected_tracks)} tracks for {current_duration / 60:.1f} minutes")
        
        # Apply crossfade
        crossfaded_path = self.processed_dir / f"{output_name}_crossfaded.mp3"
        track_paths = [t.path for t in selected_tracks]
        
        if not self.apply_crossfade(track_paths, crossfaded_path):
            return None
        
        # Normalize audio
        normalized_path = self.final_dir / f"{output_name}_normalized.mp3"
        
        if not self.normalize_audio(
            crossfaded_path,
            normalized_path,
            target_lufs=MUSIC.audio_normalization_lufs,
        ):
            return None
        
        # Trim to exact duration
        final_path = self.final_dir / f"{output_name}.mp3"
        
        if not self.trim_to_duration(normalized_path, final_path, target_seconds):
            return None
        
        # Cleanup intermediate files
        try:
            crossfaded_path.unlink()
            normalized_path.unlink()
        except Exception:
            pass
        
        logger.info(f"Playlist built: {final_path}")
        return final_path


# =============================================================================
# VIDEO ASSEMBLY
# =============================================================================

class VideoAssembly:
    """
    Assemble video clips into final montage.
    """

    def __init__(
        self,
        clips_dir: Path = VISUAL_CLIPS_DIR,
        output_dir: Path = VISUAL_FINAL_DIR,
        config: Optional[Dict] = None,
    ):
        self.clips_dir = Path(clips_dir)
        self.output_dir = Path(output_dir)
        self.config = config or {}
        
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_concat_file(
        self,
        clips: List[Path],
        loops_per_clip: int = 4,
    ) -> Path:
        """
        Create FFmpeg concat file with looped clips.
        
        Args:
            clips: List of clip paths
            loops_per_clip: Number of times to loop each clip
            
        Returns:
            Path to concat file
        """
        concat_file = self.output_dir / "concat_list.txt"
        
        with open(concat_file, "w") as f:
            for clip in clips:
                for _ in range(loops_per_clip):
                    f.write(f"file '{clip}'\n")
        
        return concat_file

    def assemble_video(
        self,
        loops_per_clip: int = 4,
        target_resolution: str = "1920x1080",
        target_fps: int = 25,
        output_name: str = "60min_video_only",
    ) -> Optional[Path]:
        """
        Assemble video clips into final montage.
        
        Args:
            loops_per_clip: Loops per clip
            target_resolution: Output resolution
            target_fps: Output FPS
            output_name: Output filename
            
        Returns:
            Path to assembled video or None
        """
        clips = sorted(self.clips_dir.glob("*.mp4"))
        
        if not clips:
            logger.error("No video clips found")
            return None
        
        logger.info(f"Assembling {len(clips)} clips with {loops_per_clip}x loops")
        
        # Create concat file
        concat_file = self.create_concat_file(clips, loops_per_clip)
        
        # Calculate expected duration
        sample_duration = self._get_clip_duration(clips[0])
        total_clips = len(clips) * loops_per_clip
        expected_duration = sample_duration * total_clips
        
        logger.info(f"Expected duration: {expected_duration / 60:.1f} minutes")
        
        # Build FFmpeg command
        output_path = self.output_dir / f"{output_name}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-vf", (
                f"scale={target_resolution.split('x')[0]}:"
                f"{target_resolution.split('x')[1]}:"
                "force_original_aspect_ratio=decrease,"
                "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
                f"fps={target_fps}"
            ),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            "-an",  # No audio in video-only file
            str(output_path),
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode != 0:
                logger.error(f"Video assembly failed: {result.stderr}")
                return None
            
            logger.info(f"Video assembled: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Video assembly error: {e}")
            return None

    def _get_clip_duration(self, clip_path: Path) -> float:
        """Get video clip duration."""
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(clip_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception:
            return 10.0  # Default to 10 seconds

    def combine_audio_video(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        video_bitrate: str = "8000k",
        audio_bitrate: str = "192k",
    ) -> bool:
        """
        Combine video and audio into final file.
        
        Args:
            video_path: Video file path
            audio_path: Audio file path
            output_path: Output file path
            video_bitrate: Video bitrate
            audio_bitrate: Audio bitrate
            
        Returns:
            True if successful
        """
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                "-b:v", video_bitrate,
                "-c:a", "aac",
                "-b:a", audio_bitrate,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-movflags", "+faststart",
                str(output_path),
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode != 0:
                logger.error(f"Combine failed: {result.stderr}")
                return False
            
            logger.info(f"Combined audio+video: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Combine error: {e}")
            return False


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_playlist_builder() -> PlaylistBuilder:
    """Factory function to create PlaylistBuilder."""
    return PlaylistBuilder()


def create_video_assembly() -> VideoAssembly:
    """Factory function to create VideoAssembly."""
    return VideoAssembly()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(get_log_path("playlist_builder")),
            logging.StreamHandler(),
        ],
    )
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        builder = create_playlist_builder()
        result = builder.build_playlist(target_minutes=60)
        print(f"Playlist built: {result}")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "assemble":
        assembly = create_video_assembly()
        result = assembly.assemble_video()
        print(f"Video assembled: {result}")