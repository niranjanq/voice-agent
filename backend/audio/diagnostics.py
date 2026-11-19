"""Microphone diagnostics and RMS audio debugging."""

from array import array
import logging
import math
from typing import Callable, Any

logger = logging.getLogger("sunrise-clinic.audio")


def attach_microphone_diagnostics(
    audio_input: Any,
    interval: int = 50,
) -> Callable[..., Any]:
    """Attach RMS level debugging callback to the local audio input transport.

    Preserves original callback while computing Root Mean Square (RMS) of audio
    samples and periodically logging signal levels.

    Args:
        audio_input: LocalAudioInputTransport instance.
        interval: Number of audio frames between diagnostic log entries.

    Returns:
        The instrumented callback function.
    """
    original_callback = audio_input._audio_in_callback
    callback_state = {"count": 0}

    def debug_audio_callback(
        in_data: bytes,
        frame_count: int,
        time_info: dict,
        status: int,
    ):
        callback_state["count"] += 1

        samples = array("h")
        samples.frombytes(in_data)

        rms = (
            math.sqrt(sum(sample * sample for sample in samples) / len(samples))
            if samples
            else 0.0
        )

        if callback_state["count"] % interval == 0:
            logger.info(
                "MIC AUDIO | count=%s | RMS=%.1f | status=%s",
                callback_state["count"],
                rms,
                status,
            )

        return original_callback(
            in_data,
            frame_count,
            time_info,
            status,
        )

    audio_input._audio_in_callback = debug_audio_callback
    logger.debug("Attached microphone diagnostics with interval %d", interval)
    return debug_audio_callback
