"""Unit tests for end-call decision logic, AudioInputGate, and EndCallProcessor.

Uses standard unittest and asyncio so no external testing framework is required.
"""

import asyncio
import unittest

from pipecat.frames.frames import (
    EndWorkerFrame,
    InputAudioRawFrame,
    TranscriptionFrame,
    TTSSpeakFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from backend.tools.end_call import (
    is_end_call_phrase,
    AudioInputGate,
    EndCallProcessor,
)


class DummyDownstreamProcessor(FrameProcessor):
    """Collector processor to immediately capture frames pushed downstream."""

    def __init__(self):
        super().__init__()
        self.received_frames = []

    async def queue_frame(self, frame, direction=FrameDirection.DOWNSTREAM, callback=None):
        self.received_frames.append(frame)


class TestEndCallPhraseDetection(unittest.TestCase):
    """Test deterministic phrase classification."""

    def test_positive_end_call_phrases(self):
        positive_cases = [
            "You can cut the call right now.",
            "Please hang up.",
            "hang up the call",
            "Goodbye.",
            "goodbye",
            "Goodbye!",
            "Bye",
            "Bye bye",
            "have a good day",
            "That's all, thank you.",
            "That's all thank you",
            "That is all, thank you.",
            "That's all, thanks.",
            "That is all, thanks",
            "I don't need anything else.",
            "I do not need anything else.",
            "don't need anything else",
            "Nothing else, thank you.",
            "nothing else thanks",
            "End the call",
            "Please end the call",
            "Cut the call",
            "Disconnect the call",
            "stop the call",
            "that's all",
            "that is all",
        ]
        for phrase in positive_cases:
            with self.subTest(phrase=phrase):
                self.assertTrue(
                    is_end_call_phrase(phrase),
                    f"Expected True for '{phrase}', got False",
                )

    def test_negative_phrases(self):
        negative_cases = [
            "No, thank you",
            "No thank you",
            "No, thanks",
            "No",
            "Don't hang up",
            "don't hang up the call",
            "Please do not cut the call",
            "never cut the call",
            "I want to hang up my coat",
            "hang up my jacket",
            "What are your clinic hours?",
            "Where is the clinic located?",
            "I want to book an appointment with Dr. Rao tomorrow.",
            "I have severe chest pain.",
            "Can you cut the fee?",
            "Can the doctor cut the price?",
            "I need help with an appointment",
            "",
            "   ",
        ]
        for phrase in negative_cases:
            with self.subTest(phrase=phrase):
                self.assertFalse(
                    is_end_call_phrase(phrase),
                    f"Expected False for '{phrase}', got True",
                )


class TestAudioInputGate(unittest.TestCase):
    """Test audio frame blocking upon termination."""

    def test_gate_allows_when_unblocked(self):
        async def run():
            gate = AudioInputGate()
            downstream = DummyDownstreamProcessor()
            gate.link(downstream)

            raw_frame = InputAudioRawFrame(
                audio=b"\x00\x00" * 10, sample_rate=16000, num_channels=1
            )
            await gate.process_frame(raw_frame, FrameDirection.DOWNSTREAM)
            self.assertEqual(len(downstream.received_frames), 1)
            self.assertEqual(downstream.received_frames[0], raw_frame)

        asyncio.run(run())

    def test_gate_drops_when_blocked(self):
        async def run():
            gate = AudioInputGate()
            downstream = DummyDownstreamProcessor()
            gate.link(downstream)

            gate.block()
            self.assertTrue(gate.is_blocked)

            raw_frame = InputAudioRawFrame(
                audio=b"\x00\x00" * 10, sample_rate=16000, num_channels=1
            )
            await gate.process_frame(raw_frame, FrameDirection.DOWNSTREAM)
            self.assertEqual(len(downstream.received_frames), 0)

        asyncio.run(run())


class TestEndCallProcessor(unittest.TestCase):
    """Test farewell emission, worker shutdown, and single-execution guarantee."""

    def test_trigger_farewell_and_end_worker(self):
        async def run():
            gate = AudioInputGate()
            processor = EndCallProcessor(
                farewell_text="Thank you for calling Sunrise Clinic. Have a good day!",
                audio_gate=gate,
            )
            downstream = DummyDownstreamProcessor()
            processor.link(downstream)

            frame = TranscriptionFrame(
                text="Please hang up now.", user_id="user", timestamp=0
            )
            await processor.process_frame(frame, FrameDirection.DOWNSTREAM)

            self.assertTrue(processor.is_call_ending)
            self.assertTrue(gate.is_blocked)

            frame_types = [type(f) for f in downstream.received_frames]
            self.assertIn(TTSSpeakFrame, frame_types)
            self.assertIn(EndWorkerFrame, frame_types)
            self.assertNotIn(TranscriptionFrame, frame_types)

            speak_frame = next(
                f for f in downstream.received_frames if isinstance(f, TTSSpeakFrame)
            )
            self.assertEqual(
                speak_frame.text,
                "Thank you for calling Sunrise Clinic. Have a good day!",
            )
            self.assertFalse(speak_frame.append_to_context)
            self.assertFalse(speak_frame.interruptible)

        asyncio.run(run())

    def test_passes_normal_transcripts(self):
        async def run():
            gate = AudioInputGate()
            processor = EndCallProcessor(audio_gate=gate)
            downstream = DummyDownstreamProcessor()
            processor.link(downstream)

            frame = TranscriptionFrame(
                text="What are your hours?", user_id="user", timestamp=0
            )
            await processor.process_frame(frame, FrameDirection.DOWNSTREAM)

            self.assertFalse(processor.is_call_ending)
            self.assertFalse(gate.is_blocked)
            self.assertEqual(len(downstream.received_frames), 1)
            self.assertEqual(downstream.received_frames[0], frame)

        asyncio.run(run())

    def test_handles_repeated_triggers_safely(self):
        async def run():
            gate = AudioInputGate()
            processor = EndCallProcessor(audio_gate=gate)
            downstream = DummyDownstreamProcessor()
            processor.link(downstream)

            frame1 = TranscriptionFrame(text="Goodbye.", user_id="user", timestamp=0)
            await processor.process_frame(frame1, FrameDirection.DOWNSTREAM)

            initial_count = len(downstream.received_frames)
            self.assertEqual(initial_count, 2)  # TTSSpeakFrame + EndWorkerFrame

            # Send repeated end call phrase
            frame2 = TranscriptionFrame(
                text="Please hang up.", user_id="user", timestamp=1
            )
            await processor.process_frame(frame2, FrameDirection.DOWNSTREAM)

            # Count must remain unchanged - no duplicate farewells
            self.assertEqual(len(downstream.received_frames), initial_count)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
