"""
transcription_service.py – AI transcription using faster-whisper.

SINGLETON PATTERN: The WhisperModel is initialised once at server startup
and reused for every request to avoid repeated RAM allocation.

CPU Optimisation:
  - model_size  = distil-large-v3   (smaller distilled model, ~250 MB)
  - device      = cpu
  - compute_type= int8              (quantised — ~2× faster on CPU)

Audio pre-processing:
  - ffmpeg normalises audio levels before transcription for better accuracy.
"""
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Singleton model holder ────────────────────────────────────────────────────
_whisper_model = None


def get_whisper_model():
    """
    Return the singleton WhisperModel instance.
    Called once at app startup (lifespan event).
    """
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info(
                "Loading faster-whisper model: size=%s device=%s compute=%s",
                settings.whisper_model_size,
                settings.whisper_device,
                settings.whisper_compute_type,
            )
            _whisper_model = WhisperModel(
                model_size_or_path=settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
            logger.info("faster-whisper model loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load faster-whisper model: %s", exc)
            _whisper_model = None
    return _whisper_model


def _normalize_audio(input_path: str, output_path: str) -> bool:
    """
    Use ffmpeg to normalise audio levels.
    Returns True on success, False on failure (graceful degradation).
    """
    try:
        cmd = [
            settings.ffmpeg_path,
            "-y",
            "-i", input_path,
            "-af", "loudnorm=I=-16:LRA=11:TP=-1.5",
            "-ar", "16000",       # resample to 16 kHz (Whisper native)
            "-ac", "1",           # mono
            "-c:a", "pcm_s16le",
            output_path,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            logger.warning("ffmpeg normalisation failed: %s", result.stderr)
            return False
        return True
    except FileNotFoundError:
        logger.warning("ffmpeg not found at '%s'. Skipping normalisation.", settings.ffmpeg_path)
        return False
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg normalisation timed out.")
        return False


class TranscriptionService:

    @staticmethod
    def transcribe(audio_bytes: bytes, original_filename: str = "audio.webm") -> str:
        """
        Accepts raw audio bytes (from /transcribe FormData upload).
        1. Saves to a temp file.
        2. Normalises with ffmpeg.
        3. Transcribes with faster-whisper.
        Returns the transcribed text.
        """
        model = get_whisper_model()
        if model is None:
            raise RuntimeError("Whisper model is not available.")

        suffix = Path(original_filename).suffix or ".webm"

        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_path = os.path.join(tmp_dir, f"raw{suffix}")
            norm_path = os.path.join(tmp_dir, "normalised.wav")

            # Write raw audio
            with open(raw_path, "wb") as f:
                f.write(audio_bytes)

            # Attempt normalisation
            use_path = norm_path if _normalize_audio(raw_path, norm_path) else raw_path

            # Transcribe
            segments, info = model.transcribe(
                use_path,
                beam_size=5,
                language="en",
                condition_on_previous_text=False,
                vad_filter=True,             # skip silence chunks
                vad_parameters={"min_silence_duration_ms": 500},
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            logger.info(
                "Transcription complete (%.1fs audio, lang=%s, prob=%.2f)",
                info.duration,
                info.language,
                info.language_probability,
            )
            return text
