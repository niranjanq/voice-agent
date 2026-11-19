"""Constructs and wires the Pipecat audio and conversational pipeline."""

from dataclasses import dataclass
import logging
from typing import Any

from pipecat.pipeline.pipeline import Pipeline
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
)
from pipecat.transports.local.audio import LocalAudioTransport

from backend.config.settings import Settings, get_settings
from backend.audio.transport import create_audio_transport
from backend.prompts.receptionist_prompt import get_receptionist_prompt
from backend.processors.vad import create_vad_processor
from backend.processors.transcription_logger import TranscriptionLogger
from backend.services.stt_service import create_stt_service
from backend.services.llm_service import create_llm_service
from backend.services.tts_service import create_tts_service
from backend.tools.end_call import AudioInputGate, EndCallProcessor

logger = logging.getLogger("sunrise-clinic.builder")


@dataclass
class PipelineComponents:
    """Encapsulates all initialized components of the receptionist pipeline."""
    pipeline: Pipeline
    transport: LocalAudioTransport
    audio_gate: AudioInputGate
    end_call_processor: EndCallProcessor
    llm_context: LLMContext
    stt_service: Any
    llm_service: Any
    tts_service: Any


def build_receptionist_pipeline(
    settings: Settings | None = None,
) -> PipelineComponents:
    """Build and configure the complete local receptionist pipeline.

    Wires together:
      audio_input -> audio_gate -> vad_processor -> stt ->
      transcription_logger -> end_call_processor -> user_aggregator ->
      llm -> tts -> audio_output -> assistant_aggregator

    Args:
        settings: Optional Settings instance. If omitted, uses global settings.

    Returns:
        PipelineComponents instance ready for execution.
    """
    if settings is None:
        settings = get_settings()

    logger.info("Building Sunrise Clinic conversational pipeline")

    # 1. Audio Transport
    transport, audio_input, audio_output = create_audio_transport(settings.audio)

    # 2. Audio input gate (allows immediate muting upon call termination)
    audio_gate = AudioInputGate()

    # 3. Voice Activity Detection (Silero VAD)
    vad_processor = create_vad_processor()

    # 4. Speech-to-Text (Faster-Whisper tiny)
    stt = create_stt_service(settings.stt)

    # 5. Transcription Logger
    transcription_logger = TranscriptionLogger()

    # 6. End-Call Processor (deterministic intent detection & farewell dispatch)
    end_call_processor = EndCallProcessor(
        farewell_text=settings.clinic.farewell_message,
        audio_gate=audio_gate,
        audio_input=audio_input,
    )

    # 7. LLM Service (Ollama qwen2.5:1.5b)
    llm = create_llm_service(settings.llm)

    # 8. TTS Service (Piper with natural speech tuning)
    tts = create_tts_service(settings.tts)

    # 9. Context & Conversation Aggregators
    system_prompt = get_receptionist_prompt(settings.clinic)
    context = LLMContext(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            }
        ]
    )
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(context)

    # 10. Assemble sequential pipeline
    pipeline = Pipeline(
        [
            audio_input,
            audio_gate,
            vad_processor,
            stt,
            transcription_logger,
            end_call_processor,
            user_aggregator,
            llm,
            tts,
            audio_output,
            assistant_aggregator,
        ]
    )

    logger.info("Pipeline constructed successfully")

    return PipelineComponents(
        pipeline=pipeline,
        transport=transport,
        audio_gate=audio_gate,
        end_call_processor=end_call_processor,
        llm_context=context,
        stt_service=stt,
        llm_service=llm,
        tts_service=tts,
    )
