"""Transcription logging processor.

Preserves the original user speech logging behavior for terminal feedback.
"""

import logging
from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

logger = logging.getLogger("sunrise-clinic.transcription")


class TranscriptionLogger(FrameProcessor):
    """Logs non-empty transcripts produced by the speech-to-text service."""

    async def process_frame(
        self,
        frame: Frame,
        direction: FrameDirection,
    ):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            transcript = frame.text.strip()
            if transcript:
                logger.info("USER SAID: %s", transcript)

        await self.push_frame(frame, direction)
