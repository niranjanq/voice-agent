"""Tools module for session management and call termination."""

from backend.tools.end_call import (
    is_end_call_phrase,
    EndCallProcessor,
    AudioInputGate,
)

__all__ = ["is_end_call_phrase", "EndCallProcessor", "AudioInputGate"]
