"""Audio transport initialization for local microphone and speaker."""

import logging
from typing import Tuple

from pipecat.transports.local.audio import (
    LocalAudioTransport,
    LocalAudioTransportParams,
)
from pipecat.processors.frame_processor import FrameProcessor

from backend.config.settings import AudioSettings, get_settings
from backend.audio.diagnostics import attach_microphone_diagnostics

logger = logging.getLogger("sunrise-clinic.audio")


def create_audio_transport(
    audio_settings: AudioSettings | None = None,
) -> Tuple[LocalAudioTransport, FrameProcessor, FrameProcessor]:
    """Initialize LocalAudioTransport, audio input, and audio output.

    Preserves configured WSL2/PulseAudio device indices and sample rates.
    Attaches microphone diagnostics if enabled in settings.

    Args:
        audio_settings: Optional AudioSettings instance. If omitted, uses global settings.

    Returns:
        Tuple of (transport, audio_input_processor, audio_output_processor).
    """
    if audio_settings is None:
        audio_settings = get_settings().audio

    in_dev_label = (
        str(audio_settings.input_device_index)
        if audio_settings.input_device_index is not None
        else "default"
    )
    out_dev_label = (
        str(audio_settings.output_device_index)
        if audio_settings.output_device_index is not None
        else "default"
    )

    logger.info(
        "Initializing LocalAudioTransport (in=%dHz, out=%dHz, in_dev=%s, out_dev=%s)",
        audio_settings.in_sample_rate,
        audio_settings.out_sample_rate,
        in_dev_label,
        out_dev_label,
    )

    transport_params = LocalAudioTransportParams(
        audio_in_enabled=audio_settings.in_enabled,
        audio_out_enabled=audio_settings.out_enabled,
        audio_in_channels=audio_settings.in_channels,
        audio_out_channels=audio_settings.out_channels,
        audio_in_sample_rate=audio_settings.in_sample_rate,
        audio_out_sample_rate=audio_settings.out_sample_rate,
        input_device_index=audio_settings.input_device_index,
        output_device_index=audio_settings.output_device_index,
    )

    transport = LocalAudioTransport(params=transport_params)

    audio_input = transport.input()
    audio_output = transport.output()

    if audio_settings.mic_diagnostics_enabled:
        attach_microphone_diagnostics(
            audio_input=audio_input,
            interval=audio_settings.mic_diagnostics_interval,
        )

    return transport, audio_input, audio_output
