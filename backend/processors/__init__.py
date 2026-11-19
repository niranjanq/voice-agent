"""Processors module for VAD, transcription logging, and frame processing."""

from backend.processors.vad import create_vad_processor
from backend.processors.transcription_logger import TranscriptionLogger

__all__ = ["create_vad_processor", "TranscriptionLogger"]
