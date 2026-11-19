"""Speech-to-Text service initialization using Faster-Whisper."""

import logging
from pipecat.services.whisper.stt import WhisperSTTService
from backend.config.settings import STTSettings, get_settings

logger = logging.getLogger("sunrise-clinic.stt")


def create_stt_service(
    stt_settings: STTSettings | None = None,
) -> WhisperSTTService:
    """Initialize Faster-Whisper STT service.

    Preserves the lightweight CPU, int8, tiny model configuration suitable
    for 8 GB RAM machines.

    Args:
        stt_settings: Optional STTSettings instance. If omitted, uses global settings.

    Returns:
        Configured WhisperSTTService.
    """
    if stt_settings is None:
        stt_settings = get_settings().stt

    logger.info(
        "Loading Whisper STT (model=%s, device=%s, compute_type=%s, language=%s)",
        stt_settings.model,
        stt_settings.device,
        stt_settings.compute_type,
        stt_settings.language,
    )

    try:
        settings = WhisperSTTService.Settings(
            model=stt_settings.model,
            language=stt_settings.language,
        )
        return WhisperSTTService(
            device=stt_settings.device,
            compute_type=stt_settings.compute_type,
            settings=settings,
        )
    except Exception:
        return WhisperSTTService(
            model=stt_settings.model,
            device=stt_settings.device,
            compute_type=stt_settings.compute_type,
            language=stt_settings.language,
        )
