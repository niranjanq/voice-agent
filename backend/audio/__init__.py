"""Audio transport and diagnostics module."""

from backend.audio.transport import create_audio_transport
from backend.audio.diagnostics import attach_microphone_diagnostics

__all__ = ["create_audio_transport", "attach_microphone_diagnostics"]
