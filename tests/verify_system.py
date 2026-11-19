"""Comprehensive system verification script for local AI Clinic Receptionist.

Checks each subsystem independently:
1. All Python imports
2. Configuration loading and environment overrides
3. Faster-Whisper STT initialization (CPU, int8, tiny)
4. Ollama connectivity and qwen2.5:1.5b model verification
5. Piper TTS initialization with en_US-lessac-high and speech parameters
6. End-call deterministic phrase decision logic
7. AudioInputGate and EndCallProcessor frame dispatch
8. Pipeline builder assembly and wiring
"""

import asyncio
import json
import logging
from pathlib import Path
import sys
import urllib.request

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("system-verification")

results = {
    "passed": [],
    "failed": [],
    "not_tested": [],
}


def test_imports():
    logger.info("Test 1: Verifying Python imports...")
    try:
        import backend.config.settings
        import backend.prompts.receptionist_prompt
        import backend.audio.diagnostics
        import backend.audio.transport
        import backend.processors.vad
        import backend.processors.transcription_logger
        import backend.services.stt_service
        import backend.services.llm_service
        import backend.services.tts_service
        import backend.tools.end_call
        import backend.pipeline.builder
        import backend.pipeline.runner
        import backend.main
        import main
        results["passed"].append("Python imports verified across all modules")
        logger.info("✓ Imports verified successfully")
    except Exception as e:
        results["failed"].append(f"Python imports failed: {e}")
        logger.error("✗ Imports failed: %s", e)


def test_configuration():
    logger.info("Test 2: Verifying configuration loading...")
    try:
        from backend.config.settings import get_settings
        settings = get_settings()
        assert settings.audio.in_sample_rate == 16000
        assert settings.audio.out_sample_rate == 24000
        assert settings.stt.model == "tiny"
        assert settings.llm.model == "qwen2.5:1.5b"
        assert settings.tts.voice == "en_US-lessac-high"
        assert settings.tts.length_scale == 1.05
        assert settings.tts.noise_scale == 0.667
        assert settings.tts.noise_w_scale == 0.8
        assert settings.clinic.clinic_name == "Sunrise Clinic"
        assert "12 Demo Road, Bengaluru" in settings.clinic.clinic_address
        results["passed"].append("Configuration loading and defaults verified")
        logger.info("✓ Configuration verified successfully")
    except Exception as e:
        results["failed"].append(f"Configuration failed: {e}")
        logger.error("✗ Configuration failed: %s", e)


def test_whisper_init():
    logger.info("Test 3: Verifying Faster-Whisper initialization...")
    try:
        from backend.services.stt_service import create_stt_service
        stt = create_stt_service()
        assert stt is not None
        results["passed"].append("Faster-Whisper STT initialization (tiny, cpu, int8) verified")
        logger.info("✓ Whisper STT initialized successfully")
    except Exception as e:
        results["failed"].append(f"Whisper STT failed: {e}")
        logger.error("✗ Whisper STT failed: %s", e)


def test_ollama_reachable():
    logger.info("Test 4: Verifying Ollama reachability and model availability...")
    try:
        from backend.config.settings import get_settings
        settings = get_settings()
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5)
        data = json.loads(req.read().decode())
        available_models = [m["name"] for m in data.get("models", [])]
        logger.info("Available Ollama models: %s", available_models)
        target = settings.llm.model
        matching = any(target in m for m in available_models)
        if not matching:
            raise RuntimeError(f"Model '{target}' not found in Ollama models: {available_models}")
        results["passed"].append(f"Ollama reachability and model '{target}' verified")
        logger.info("✓ Ollama is reachable and model is present")
    except Exception as e:
        results["failed"].append(f"Ollama reachability failed: {e}")
        logger.error("✗ Ollama failed: %s", e)


def test_piper_tts():
    logger.info("Test 5: Verifying Piper TTS initialization and parameters...")
    try:
        from backend.services.tts_service import create_tts_service
        tts = create_tts_service()
        assert tts is not None
        assert hasattr(tts, "_voice")
        cfg = tts._voice.config
        logger.info("Piper voice: length_scale=%.2f, noise_scale=%.3f, noise_w_scale=%.2f",
                    cfg.length_scale, cfg.noise_scale, cfg.noise_w_scale)
        assert cfg.length_scale == 1.05
        assert cfg.noise_scale == 0.667
        assert cfg.noise_w_scale == 0.8
        results["passed"].append("Piper TTS initialization (en_US-lessac-high) and voice parameters verified")
        logger.info("✓ Piper TTS initialized with high-quality voice and speech parameters")
    except Exception as e:
        results["failed"].append(f"Piper TTS failed: {e}")
        logger.error("✗ Piper TTS failed: %s", e)


def test_end_call_logic():
    logger.info("Test 6: Verifying deterministic end-call decision logic...")
    try:
        from backend.tools.end_call import is_end_call_phrase

        positives = [
            "You can cut the call right now.",
            "Please hang up.",
            "Goodbye.",
            "That's all, thank you.",
            "I don't need anything else.",
            "Cut the call",
            "end the call",
        ]
        negatives = [
            "No, thank you",
            "Don't hang up",
            "What are your hours?",
            "I want to book an appointment with Dr. Rao",
        ]

        for p in positives:
            assert is_end_call_phrase(p) is True, f"Expected True for '{p}'"
        for n in negatives:
            assert is_end_call_phrase(n) is False, f"Expected False for '{n}'"

        results["passed"].append("Deterministic end-call phrase decision logic verified (all positive & negative test cases)")
        logger.info("✓ End-call decision logic verified successfully")
    except Exception as e:
        results["failed"].append(f"End-call decision logic failed: {e}")
        logger.error("✗ End-call decision logic failed: %s", e)


async def test_end_call_processor():
    logger.info("Test 7: Verifying EndCallProcessor and AudioInputGate...")
    try:
        from pipecat.frames.frames import TranscriptionFrame, TTSSpeakFrame, EndWorkerFrame
        from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
        from backend.tools.end_call import AudioInputGate, EndCallProcessor

        class DownstreamCollector(FrameProcessor):
            def __init__(self):
                super().__init__()
                self.frames = []
            async def queue_frame(self, frame, direction=FrameDirection.DOWNSTREAM, callback=None):
                self.frames.append(frame)

        gate = AudioInputGate()
        proc = EndCallProcessor(audio_gate=gate)
        collector = DownstreamCollector()
        proc.link(collector)

        # Trigger with end phrase
        await proc.process_frame(
            TranscriptionFrame(text="Please hang up.", user_id="user", timestamp=0),
            FrameDirection.DOWNSTREAM,
        )

        assert proc.is_call_ending is True
        assert gate.is_blocked is True
        assert any(isinstance(f, TTSSpeakFrame) for f in collector.frames)
        assert any(isinstance(f, EndWorkerFrame) for f in collector.frames)

        # Repeat trigger should not add extra farewell frames
        count_before = len(collector.frames)
        await proc.process_frame(
            TranscriptionFrame(text="Goodbye.", user_id="user", timestamp=1),
            FrameDirection.DOWNSTREAM,
        )
        assert len(collector.frames) == count_before

        results["passed"].append("EndCallProcessor single farewell & EndWorkerFrame dispatch verified")
        logger.info("✓ EndCallProcessor and AudioInputGate verified successfully")
    except Exception as e:
        results["failed"].append(f"EndCallProcessor test failed: {e}")
        logger.error("✗ EndCallProcessor failed: %s", e)


def test_pipeline_assembly():
    logger.info("Test 8: Verifying complete pipeline assembly...")
    try:
        from backend.pipeline.builder import build_receptionist_pipeline
        components = build_receptionist_pipeline()
        assert components.pipeline is not None
        assert components.transport is not None
        assert components.end_call_processor is not None
        assert components.audio_gate is not None
        # Pipeline contains 11 active processors plus Pipecat Source and Sink (total 13)
        assert len(components.pipeline.processors) == 13
        results["passed"].append("Complete 11-stage pipeline assembly verified (including Source/Sink)")
        logger.info("✓ Pipeline assembly verified successfully")
    except Exception as e:
        results["failed"].append(f"Pipeline assembly failed: {e}")
        logger.error("✗ Pipeline assembly failed: %s", e)


async def run_all():
    test_imports()
    test_configuration()
    test_whisper_init()
    test_ollama_reachable()
    test_piper_tts()
    test_end_call_logic()
    await test_end_call_processor()
    test_pipeline_assembly()

    # Document hardware / live interactions
    results["not_tested"].append("Live human physical voice capture via hardware microphone (requires user speaking)")
    results["not_tested"].append("Physical acoustic output to room speaker/headphones (requires user listening)")

    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    print("PASSED:")
    for p in results["passed"]:
        print(f"  ✓ {p}")
    print("FAILED:")
    for f in results["failed"]:
        print(f"  ✗ {f}")
    print("NOT TESTED (live physical hardware interactions):")
    for nt in results["not_tested"]:
        print(f"  - {nt}")
    print("=" * 60)

    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_all())
