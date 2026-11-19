<<<<<<< HEAD
# Local AI Clinic Receptionist (Modular Python Architecture)

A fully local voice demonstration using Pipecat 1.15.0, Faster-Whisper, Ollama (Qwen2.5 1.5B), Piper TTS, and Silero VAD.
Operates with zero cloud dependencies and no paid API keys. All speech recognition, inference, voice activity detection, and speech synthesis execute completely offline on local hardware.

## Project Structure

```text
clinic_receptionist_local/
│
├── main.py                          # Top-level entry point
├── requirements.txt                 # Pinned dependencies
├── README.md                        # Documentation and instructions
│
├── backend/
│   ├── __init__.py
│   ├── main.py                      # Application bootstrap & logging setup
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py              # Centralized configuration & environment variables
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── receptionist_prompt.py   # Clinic system prompt & clinical rules
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── transport.py             # LocalAudioTransport initialization
│   │   └── diagnostics.py           # RMS mic signal diagnostics
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── vad.py                   # Silero VAD processor
│   │   └── transcription_logger.py  # User speech transcription logger
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stt_service.py           # Faster-Whisper STT (tiny, cpu, int8)
│   │   ├── llm_service.py           # Local Ollama client (qwen2.5:1.5b)
│   │   └── tts_service.py           # Piper TTS with high-quality voice & natural speech tuning
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   └── end_call.py              # Deterministic end-call detector, AudioInputGate & EndCallProcessor
│   │
│   └── pipeline/
│       ├── __init__.py
│       ├── builder.py               # Sequential pipeline assembly (11 processors)
│       └── runner.py                # Pipeline task execution & lifecycle management
│
└── tests/
    ├── __init__.py
    ├── test_configuration.py        # Settings and prompt unit tests
    ├── test_end_call.py             # Phrase classification & gate/processor unit tests
    └── verify_system.py             # Full subsystem verification script
```

## System Requirements

- Windows 11 with WSL2 (Ubuntu 24.04 recommended)
- Python 3.12 or 3.13 in a virtual environment (`.venv`)
- 8 GB RAM (optimized for lightweight models on CPU)
- Local Ollama running with `qwen2.5:1.5b`
- Microphone and speakers or headphones (headphones recommended to prevent feedback)

## Quick Start

### 1. Ensure Ollama is running with Qwen 2.5 (1.5B)

```powershell
ollama pull qwen2.5:1.5b
ollama run qwen2.5:1.5b
```

Verify that Ollama responds, type `/bye`, and keep the Ollama service active.

### 2. Activate Virtual Environment

**In Windows PowerShell:**
```powershell
cd clinic_receptionist_local
.\.venv\Scripts\Activate.ps1
```

**In WSL2 Ubuntu:**
```bash
cd /mnt/d/AI/clinic_receptionist_local/clinic_receptionist_local
source .venv/bin/activate
```

### 3. Run the Receptionist

```bash
python main.py
```
*(or `python backend/main.py`)*

### 4. Running Tests

To run the unit test suite:
```bash
python -m unittest discover tests
```

To run complete system verification:
```bash
python tests/verify_system.py
```

## End-Call Session Termination

When the caller says an explicit departure phrase, the system deterministically intercepts the intent:
- **Trigger phrases**:
  - "Please hang up."
  - "You can cut the call right now."
  - "Goodbye." / "Bye bye"
  - "That's all, thank you." / "That is all, thanks."
  - "I don't need anything else."
  - "Cut the call." / "End the call."
- **Guarantees**:
  1. The user's input is withheld from the LLM so no stray tokens or secondary answers are generated.
  2. The `AudioInputGate` drops any further microphone frames and stops the input stream.
  3. The `EndCallProcessor` emits an uninterruptible farewell `TTSSpeakFrame`:
     *"Thank you for calling Sunrise Clinic. Have a good day!"*
  4. An `EndWorkerFrame` is pushed downstream behind the farewell speech.
  5. The audio output transport finishes playing the farewell audio to the speaker before the pipeline completes.
  6. PyAudio and transport resources are released gracefully upon exit.
  7. Phrases such as *"No, thank you"* or *"Don't hang up"* do not trigger termination.

## Voice Quality Improvements

1. **High-Definition Voice**: Configured with `en_US-lessac-high` (with automatic fallback to `en_US-lessac-medium`).
2. **Pacing & Cadence Tuning**:
   - `length_scale = 1.05`: Slightly relaxed, natural receptionist tempo that prevents robotic rapid-fire delivery.
   - `noise_scale = 0.667`: Natural phoneme fluctuation.
   - `noise_w_scale = 0.80`: Natural duration variability between phonemes.
3. **Conversational Prompting**:
   - Short one-to-two sentence responses.
   - Natural contractions (e.g. *I'm*, *we're*, *don't*).
   - Asking only one question at a time.
   - Zero markdown, bullet points, asterisks, or formatting symbols in spoken responses.

## Clinic Details (Fictional Demonstration)

- **Name**: Sunrise Clinic
- **Hours**: Monday to Saturday, 9 AM to 6 PM
- **Address**: 12 Demo Road, Bengaluru
- **Consultation Fee**: 500 rupees
- **Appointment Policy**: Demonstration request only; no appointments are booked, calendars checked, or medical advice provided.
=======
# voice-agent
A modular, locally hosted AI voice agent built with Python and Pipecat, integrating Whisper for speech recognition, Ollama for LLM inference, and Piper for text-to-speech. Supports real-time voice conversations with open-source technologies.
>>>>>>> 58e6ad21fd21f814fc0f79fa024311dda757a902
