"""Text-to-Speech service initialization using Piper."""

import logging
from pipecat.services.piper.tts import PiperTTSService
from backend.config.settings import TTSSettings, get_settings

logger = logging.getLogger("sunrise-clinic.tts")


def create_tts_service(
    tts_settings: TTSSettings | None = None,
) -> PiperTTSService:
    """Initialize Piper TTS service with improved voice quality settings.

    Attempts to load high-quality voice (en_US-lessac-high), falling back to
    medium quality (en_US-lessac-medium) if loading fails. Configures natural
    speech pacing and phoneme parameters.

    Args:
        tts_settings: Optional TTSSettings instance. If omitted, uses global settings.

    Returns:
        Configured PiperTTSService.
    """
    if tts_settings is None:
        tts_settings = get_settings().tts

    selected_voice = tts_settings.voice

    try:
        logger.info("Initializing Piper TTS with voice '%s'", selected_voice)
        service = _init_piper(selected_voice)
    except Exception as e:
        logger.warning(
            "Failed to load preferred voice '%s' (%s). Falling back to '%s'",
            selected_voice,
            e,
            tts_settings.fallback_voice,
        )
        selected_voice = tts_settings.fallback_voice
        service = _init_piper(selected_voice)

    # Apply voice parameters for natural speech cadence and pronunciation
    if hasattr(service, "_voice") and hasattr(service._voice, "config"):
        cfg = service._voice.config
        cfg.length_scale = tts_settings.length_scale
        cfg.noise_scale = tts_settings.noise_scale
        cfg.noise_w_scale = tts_settings.noise_w_scale
        logger.info(
            "Configured Piper voice parameters: length_scale=%.2f, noise_scale=%.3f, noise_w_scale=%.2f",
            cfg.length_scale,
            cfg.noise_scale,
            cfg.noise_w_scale,
        )

    return service


def _init_piper(voice_name: str) -> PiperTTSService:
    """Instantiate PiperTTSService using modern settings API with fallback."""
    try:
        settings = PiperTTSService.Settings(voice=voice_name)
        return PiperTTSService(settings=settings)
    except Exception:
        return PiperTTSService(voice_id=voice_name)
