"""Deterministic end-call detection and graceful session termination.

Provides robust natural language phrase matching, an AudioInputGate to drop
incoming microphone frames upon termination, and an EndCallProcessor that
emits the final farewell TTS frame and graceful EndWorkerFrame.
"""

import logging
import re
from typing import Any, Optional

from pipecat.frames.frames import (
    EndWorkerFrame,
    Frame,
    InputAudioRawFrame,
    TranscriptionFrame,
    TTSSpeakFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from backend.config.settings import get_settings

logger = logging.getLogger("sunrise-clinic.end_call")

# Negation patterns that disqualify end-call matching
NEGATION_REGEX = re.compile(
    r"\b(don'?t|do not|never|shouldn'?t|not|won'?t)\s+(hang\s*up|cut\s+the\s+call|end\s+the\s+call|disconnect)",
    re.IGNORECASE,
)

# Unrelated contexts where "hang up" or "cut" might appear innocently
UNRELATED_REGEX = re.compile(
    r"\b(hang\s*up\s+my|cut\s+(the\s+fee|the\s+price|the\s+cost|paper|bread|hair|power))\b",
    re.IGNORECASE,
)

# Explicit termination intents
EXPLICIT_END_PATTERNS = [
    # Direct farewells
    re.compile(r"^\s*(good\s*bye|bye\s*bye|bye|have a good day)\b", re.IGNORECASE),
    re.compile(r"\b(good\s*bye|bye\s*bye)\s*[\.!\?]?\s*$", re.IGNORECASE),

    # Hang up commands
    re.compile(r"\b(please\s+)?(hang\s*up)(\s+the\s+call|\s+now)?\b", re.IGNORECASE),

    # Cut call commands
    re.compile(r"\b(you\s+can\s+)?cut\s+the\s+call(\s+right\s+now|\s+now)?\b", re.IGNORECASE),

    # End / disconnect / stop call commands
    re.compile(r"\b(please\s+)?(end|disconnect|close|stop|terminate)\s+the\s+call\b", re.IGNORECASE),
    re.compile(r"\b(end|disconnect)\s+call\b", re.IGNORECASE),

    # "That's all" / "Nothing else" combinations
    re.compile(r"\b(that'?s|that\s+is)\s+all(\s*,\s*|\s+)(thank\s*you|thanks)\b", re.IGNORECASE),
    re.compile(r"\bthat\s*will\s*be\s*all(\s*,\s*|\s+)(thank\s*you|thanks)\b", re.IGNORECASE),
    re.compile(r"^\s*(that'?s|that\s+is)\s+all\s*[\.!\?]?\s*$", re.IGNORECASE),
    re.compile(r"\b(i\s+)?(don'?t|do\s+not)\s+need\s+anything\s+else\b", re.IGNORECASE),
    re.compile(r"\bnothing\s+else(\s*,\s*|\s+)(thank\s*you|thanks)\b", re.IGNORECASE),
    re.compile(r"^\s*nothing\s+else\s*[\.!\?]?\s*$", re.IGNORECASE),
]


def is_end_call_phrase(text: str) -> bool:
    """Determine whether user input expresses an explicit intent to end the call.

    Distinguishes explicit termination phrases from ambiguous statements like
    'No, thank you' and handles negations like 'Don't hang up'.

    Args:
        text: Transcribed user speech text.

    Returns:
        True if the text contains an explicit end-call request, False otherwise.
    """
    cleaned = text.strip()
    if not cleaned:
        return False

    # Check for negations first (e.g. "Don't hang up")
    if NEGATION_REGEX.search(cleaned):
        return False

    # Check for unrelated idioms (e.g. "hang up my coat")
    if UNRELATED_REGEX.search(cleaned):
        return False

    # Never treat a simple "no, thank you" as call termination
    normalized = re.sub(r"[^\w\s]", "", cleaned).strip().lower()
    if normalized in ("no thank you", "no thanks", "no"):
        return False

    # Check explicit patterns
    for pattern in EXPLICIT_END_PATTERNS:
        if pattern.search(cleaned):
            return True

    return False


class AudioInputGate(FrameProcessor):
    """Pipeline processor placed after audio input to instantly block mic frames on shutdown."""

    def __init__(self):
        super().__init__()
        self._is_blocked = False

    def block(self):
        """Block any further audio frames from passing through."""
        self._is_blocked = True
        logger.debug("AudioInputGate: Microphone frames blocked")

    def unblock(self):
        """Unblock audio frames."""
        self._is_blocked = False

    @property
    def is_blocked(self) -> bool:
        return self._is_blocked

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if self._is_blocked and isinstance(frame, InputAudioRawFrame):
            # Drop incoming microphone audio frame
            return

        await self.push_frame(frame, direction)


class EndCallProcessor(FrameProcessor):
    """Monitors transcripts, intercepts end-call intents, delivers farewell, and terminates."""

    def __init__(
        self,
        farewell_text: Optional[str] = None,
        audio_gate: Optional[AudioInputGate] = None,
        audio_input: Optional[Any] = None,
    ):
        super().__init__()
        settings = get_settings()
        self._farewell_text = farewell_text or settings.clinic.farewell_message
        self._audio_gate = audio_gate
        self._audio_input = audio_input
        self._call_ending = False

    @property
    def is_call_ending(self) -> bool:
        return self._call_ending

    async def trigger_end_call(self):
        """Programmatically trigger session termination with farewell."""
        if self._call_ending:
            logger.debug("End call already in progress; ignoring duplicate trigger.")
            return

        self._call_ending = True
        logger.info("Triggering end-call sequence: delivering farewell and shutting down.")

        # 1. Stop accepting further microphone input
        if self._audio_gate:
            self._audio_gate.block()

        if self._audio_input and hasattr(self._audio_input, "_in_stream"):
            try:
                if self._audio_input._in_stream and self._audio_input._in_stream.is_active():
                    self._audio_input._in_stream.stop_stream()
                    logger.debug("Stopped PyAudio input stream")
            except Exception as e:
                logger.warning("Error stopping audio input stream: %s", e)

        # 2. Deliver one short farewell via TTS (uninterruptible)
        farewell_frame = TTSSpeakFrame(
            text=self._farewell_text,
            append_to_context=False,
        )
        farewell_frame.interruptible = False
        await self.push_frame(farewell_frame)

        # 3. Gracefully terminate the pipeline worker after audio plays
        await self.push_frame(EndWorkerFrame())

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # Drop any transcription frames if call is already terminating
        if self._call_ending and isinstance(frame, TranscriptionFrame):
            return

        if isinstance(frame, TranscriptionFrame):
            transcript = frame.text.strip()
            if is_end_call_phrase(transcript):
                logger.info(
                    "Explicit end-call phrase detected: '%s'. Terminating session.",
                    transcript,
                )
                await self.trigger_end_call()
                # Crucial: Do NOT push this frame downstream to LLM
                return

        await self.push_frame(frame, direction)
