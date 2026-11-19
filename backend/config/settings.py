"""Application configuration and environment settings.

Centralizes all hardware, model, and clinic settings with environment variable
support and safe local defaults.
"""

from dataclasses import dataclass, field
import os
from typing import Optional


@dataclass
class AudioSettings:
    """Audio hardware and transport parameters."""
    in_enabled: bool = True
    out_enabled: bool = True
    in_channels: int = 1
    out_channels: int = 1
    in_sample_rate: int = 16000
    out_sample_rate: int = 24000
    input_device_index: Optional[int] = None
    output_device_index: Optional[int] = None
    mic_diagnostics_enabled: bool = True
    mic_diagnostics_interval: int = 50


@dataclass
class STTSettings:
    """Speech-to-Text configuration using Faster-Whisper."""
    model: str = "tiny"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str = "en"


@dataclass
class LLMSettings:
    """Language model configuration using local Ollama."""
    model: str = "qwen2.5:1.5b"
    base_url: str = "http://localhost:11434/v1"


@dataclass
class TTSSettings:
    """Text-to-Speech configuration using Piper."""
    voice: str = "en_US-lessac-high"
    fallback_voice: str = "en_US-lessac-medium"
    length_scale: float = 1.05  # Natural, slightly relaxed cadence (default: 1.0)
    noise_scale: float = 0.667  # Natural phoneme variability
    noise_w_scale: float = 0.8  # Natural phoneme duration variability


@dataclass
class ClinicSettings:
    """Fictional clinic administrative details and policies."""
    clinic_name: str = "Sunrise Clinic"
    clinic_hours: str = "Monday to Saturday, 9 AM to 6 PM"
    clinic_address: str = "12 Demo Road, Bengaluru"
    consultation_fee: str = "500 rupees"
    farewell_message: str = "Thank you for calling Sunrise Clinic. Have a good day!"


@dataclass
class Settings:
    """Global configuration settings for the receptionist."""
    audio: AudioSettings = field(default_factory=AudioSettings)
    stt: STTSettings = field(default_factory=STTSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    tts: TTSSettings = field(default_factory=TTSSettings)
    clinic: ClinicSettings = field(default_factory=ClinicSettings)
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        """Instantiate settings with optional environment variable overrides."""
        raw_in_dev = os.getenv("AUDIO_INPUT_DEVICE_INDEX")
        raw_out_dev = os.getenv("AUDIO_OUTPUT_DEVICE_INDEX")
        in_dev = int(raw_in_dev) if raw_in_dev is not None and raw_in_dev.strip() != "" else None
        out_dev = int(raw_out_dev) if raw_out_dev is not None and raw_out_dev.strip() != "" else None

        audio = AudioSettings(
            in_enabled=os.getenv("AUDIO_IN_ENABLED", "true").lower() == "true",
            out_enabled=os.getenv("AUDIO_OUT_ENABLED", "true").lower() == "true",
            in_channels=int(os.getenv("AUDIO_IN_CHANNELS", "1")),
            out_channels=int(os.getenv("AUDIO_OUT_CHANNELS", "1")),
            in_sample_rate=int(os.getenv("AUDIO_IN_SAMPLE_RATE", "16000")),
            out_sample_rate=int(os.getenv("AUDIO_OUT_SAMPLE_RATE", "24000")),
            input_device_index=in_dev,
            output_device_index=out_dev,
            mic_diagnostics_enabled=os.getenv("MIC_DIAGNOSTICS_ENABLED", "true").lower() == "true",
            mic_diagnostics_interval=int(os.getenv("MIC_DIAGNOSTICS_INTERVAL", "50")),
        )

        stt = STTSettings(
            model=os.getenv("STT_MODEL", "tiny"),
            device=os.getenv("STT_DEVICE", "cpu"),
            compute_type=os.getenv("STT_COMPUTE_TYPE", "int8"),
            language=os.getenv("STT_LANGUAGE", "en"),
        )

        llm = LLMSettings(
            model=os.getenv("LLM_MODEL", "qwen2.5:1.5b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        )

        tts = TTSSettings(
            voice=os.getenv("TTS_VOICE", "en_US-lessac-high"),
            fallback_voice=os.getenv("TTS_FALLBACK_VOICE", "en_US-lessac-medium"),
            length_scale=float(os.getenv("TTS_LENGTH_SCALE", "1.05")),
            noise_scale=float(os.getenv("TTS_NOISE_SCALE", "0.667")),
            noise_w_scale=float(os.getenv("TTS_NOISE_W_SCALE", "0.8")),
        )

        clinic = ClinicSettings(
            clinic_name=os.getenv("CLINIC_NAME", "Sunrise Clinic"),
            clinic_hours=os.getenv("CLINIC_HOURS", "Monday to Saturday, 9 AM to 6 PM"),
            clinic_address=os.getenv("CLINIC_ADDRESS", "12 Demo Road, Bengaluru"),
            consultation_fee=os.getenv("CONSULTATION_FEE", "500 rupees"),
            farewell_message=os.getenv(
                "FAREWELL_MESSAGE",
                "Thank you for calling Sunrise Clinic. Have a good day!",
            ),
        )

        return cls(
            audio=audio,
            stt=stt,
            llm=llm,
            tts=tts,
            clinic=clinic,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


_global_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retrieve singleton configuration instance."""
    global _global_settings
    if _global_settings is None:
        _global_settings = Settings.from_env()
    return _global_settings
