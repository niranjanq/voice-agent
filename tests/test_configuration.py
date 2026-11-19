"""Unit tests for configuration loading and system prompt formatting."""

import os
import unittest
from unittest import mock

from backend.config.settings import Settings
from backend.prompts.receptionist_prompt import get_receptionist_prompt


class TestConfiguration(unittest.TestCase):
    """Test configuration defaults and overrides."""

    def test_default_settings(self):
        settings = Settings()

        # Audio defaults
        self.assertEqual(settings.audio.in_sample_rate, 16000)
        self.assertEqual(settings.audio.out_sample_rate, 24000)
        self.assertEqual(settings.audio.in_channels, 1)
        self.assertEqual(settings.audio.out_channels, 1)
        self.assertIsNone(settings.audio.input_device_index)
        self.assertIsNone(settings.audio.output_device_index)

        # STT defaults (Faster-Whisper on CPU with 8GB RAM)
        self.assertEqual(settings.stt.model, "tiny")
        self.assertEqual(settings.stt.device, "cpu")
        self.assertEqual(settings.stt.compute_type, "int8")
        self.assertEqual(settings.stt.language, "en")

        # LLM defaults (Ollama local)
        self.assertEqual(settings.llm.model, "qwen2.5:1.5b")
        self.assertEqual(settings.llm.base_url, "http://localhost:11434/v1")

        # TTS defaults (Piper high quality voice with tuned speech parameters)
        self.assertEqual(settings.tts.voice, "en_US-lessac-high")
        self.assertEqual(settings.tts.fallback_voice, "en_US-lessac-medium")
        self.assertEqual(settings.tts.length_scale, 1.05)
        self.assertEqual(settings.tts.noise_scale, 0.667)
        self.assertEqual(settings.tts.noise_w_scale, 0.8)

        # Clinic defaults
        self.assertEqual(settings.clinic.clinic_name, "Sunrise Clinic")
        self.assertIn("12 Demo Road, Bengaluru", settings.clinic.clinic_address)
        self.assertIn("500 rupees", settings.clinic.consultation_fee)

    def test_settings_environment_override(self):
        env_vars = {
            "LLM_MODEL": "custom-model:latest",
            "TTS_VOICE": "en_US-custom-high",
            "TTS_LENGTH_SCALE": "1.10",
            "AUDIO_INPUT_DEVICE_INDEX": "2",
            "CLINIC_NAME": "Test Health Center",
        }
        with mock.patch.dict(os.environ, env_vars, clear=False):
            settings = Settings.from_env()
            self.assertEqual(settings.llm.model, "custom-model:latest")
            self.assertEqual(settings.tts.voice, "en_US-custom-high")
            self.assertEqual(settings.tts.length_scale, 1.10)
            self.assertEqual(settings.audio.input_device_index, 2)
            self.assertEqual(settings.clinic.clinic_name, "Test Health Center")

    def test_receptionist_prompt_content(self):
        prompt = get_receptionist_prompt()

        # Clinic info
        self.assertIn("Sunrise Clinic", prompt)
        self.assertIn("12 Demo Road, Bengaluru", prompt)
        self.assertIn("500 rupees", prompt)
        self.assertIn("Monday to Saturday, 9 AM to 6 PM", prompt)

        # Appointment details collection
        self.assertIn("Patient name", prompt)
        self.assertIn("Requested doctor", prompt)
        self.assertIn("Preferred date and time", prompt)

        # Demonstration & non-booking safeguard
        self.assertIn(
            "demonstration request and no appointment has actually been booked",
            prompt,
        )

        # Medical safeguards
        self.assertIn("Do not diagnose", prompt)
        self.assertIn("recommend medicines", prompt)
        self.assertIn("emergency", prompt)


if __name__ == "__main__":
    unittest.main()
