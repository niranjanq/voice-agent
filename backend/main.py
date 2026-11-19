"""Sunrise Clinic Local AI Receptionist - Main Entry Point.

Modular architecture coordinating audio transport, Silero VAD, Faster-Whisper,
Ollama LLM, Piper TTS, and deterministic end-call session termination.
"""

import asyncio
import logging
import sys

from backend.config.settings import get_settings
from backend.pipeline.builder import build_receptionist_pipeline
from backend.pipeline.runner import run_pipeline


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure structured console logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger("sunrise-clinic")


async def main() -> None:
    """Initialize configuration, build pipeline components, and run the receptionist."""
    settings = get_settings()
    logger = setup_logging(settings.log_level)

    logger.info("Starting Sunrise Clinic Receptionist (Modular Architecture)")
    try:
        components = build_receptionist_pipeline(settings)
        await run_pipeline(components)
    except KeyboardInterrupt:
        logger.info("Receptionist stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logger.exception("Fatal error during receptionist operation: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
