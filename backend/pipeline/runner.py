"""Execution runner for the Sunrise Clinic Receptionist pipeline."""

import asyncio
import logging

from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner

from backend.pipeline.builder import PipelineComponents

logger = logging.getLogger("sunrise-clinic.runner")


def validate_audio_hardware() -> None:
    """Pre-flight check to verify that audio devices exist before running pipeline.

    Prevents low-level PortAudio C-library segmentation faults in headless
    or misconfigured environments like unbridged WSL2.
    """
    try:
        import pyaudio

        p = pyaudio.PyAudio()
        try:
            device_count = p.get_device_count()
        finally:
            p.terminate()

        if device_count == 0:
            raise RuntimeError(
                "No audio input or output devices were detected by PortAudio.\n"
                "  * If running in WSL2: configure PulseAudio / WSLg audio forwarding\n"
                "    (e.g. export PULSE_SERVER=unix:/mnt/wslg/runtime-dir/pulse/native)\n"
                "  * Or run the application directly on Windows PowerShell (python main.py)."
            )
        logger.debug("PortAudio detected %d available audio device(s).", device_count)
    except RuntimeError:
        raise
    except Exception as e:
        logger.debug("PortAudio hardware pre-check skipped: %s", e)


async def run_pipeline(components: PipelineComponents) -> None:
    """Run the receptionist pipeline task until termination or interrupt.

    Handles startup notification, task execution, graceful completion,
    and transport cleanup.

    Args:
        components: Initialized PipelineComponents from builder.
    """
    validate_audio_hardware()

    task = PipelineTask(components.pipeline)
    runner = PipelineRunner()

    logger.info("========================================")
    logger.info("SUNRISE CLINIC RECEPTIONIST READY")
    logger.info("Speak into your microphone.")
    logger.info("To end the call, say: 'Goodbye', 'Please hang up', or 'That is all, thank you.'")
    logger.info("Press CTRL+C to force stop.")
    logger.info("========================================")

    try:
        await runner.add_workers(task)
        await runner.run()
        logger.info("Session completed successfully.")
    except asyncio.CancelledError:
        logger.info("Pipeline task cancelled.")
    except Exception as e:
        logger.exception("Unexpected error during pipeline execution: %s", e)
        raise
    finally:
        logger.info("Releasing audio resources and cleaning up...")
        try:
            if hasattr(components.transport, "cleanup"):
                await components.transport.cleanup()
        except Exception as e:
            logger.debug("Error during transport cleanup: %s", e)
        logger.info("Cleanup complete.")
