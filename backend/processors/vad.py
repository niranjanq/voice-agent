"""Voice Activity Detection (VAD) initialization with Silero."""

import logging
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.audio.vad_processor import VADProcessor

logger = logging.getLogger("sunrise-clinic.vad")


def create_vad_processor() -> VADProcessor:
    """Initialize Silero VAD analyzer and wrapper processor.

    Returns:
        Configured VADProcessor instance.
    """
    logger.info("Initializing Silero VAD analyzer")
    vad_analyzer = SileroVADAnalyzer()
    return VADProcessor(vad_analyzer=vad_analyzer)
