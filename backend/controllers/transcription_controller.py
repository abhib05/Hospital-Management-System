"""
transcription_controller.py – /api/transcribe endpoint.
Accepts audio via multipart FormData, returns transcribed text.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.auth.rbac import require_doctor, CurrentUser
from backend.services.transcription_service import TranscriptionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Transcription"])

ALLOWED_AUDIO_TYPES = {
    "audio/webm", "audio/ogg", "audio/wav",
    "audio/mpeg", "audio/mp4", "audio/x-m4a",
    "application/octet-stream",  # Some browsers use generic type
}
MAX_AUDIO_SIZE_MB = 25


@router.post("/transcribe")
async def transcribe_audio(
    audio: Annotated[UploadFile, File(description="Audio file (.webm, .wav, .mp3)")],
    current_user: Annotated[CurrentUser, Depends(require_doctor)],
):
    """
    Doctors only.  Accepts MediaRecorder .webm from the frontend.
    Returns { "text": "..." }.
    The frontend shows a spinner while this request is in-flight.
    """
    # Validate file size
    audio_bytes = await audio.read()
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > MAX_AUDIO_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file too large ({size_mb:.1f} MB). Max {MAX_AUDIO_SIZE_MB} MB.",
        )

    logger.info(
        "Transcription request from user_id=%d, file=%s, size=%.2f MB",
        current_user.user_id,
        audio.filename,
        size_mb,
    )

    try:
        text = TranscriptionService.transcribe(audio_bytes, audio.filename or "audio.webm")
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return {"text": text, "filename": audio.filename}
