"""Tests for AnyRobo."""

import unittest
from typing import Any
from unittest.mock import patch

from anyrobo import AnyRobo


class TestAnyRobo(unittest.TestCase):
    """Tests for the AnyRobo class."""

    @patch("anyrobo.speech.recognition.SpeechRecognizer")
    @patch("anyrobo.speech.synthesis.TextToSpeech")
    def test_init(self, mock_tts: Any, mock_recognizer: Any) -> None:
        """Test initialization with default parameters."""
        assistant: AnyRobo = AnyRobo()

        self.assertEqual(assistant.SAMPLE_RATE, 24000)
        self.assertEqual(assistant.SILENCE_THRESHOLD, 0.02)
        self.assertEqual(assistant.SILENCE_DURATION, 1.5)
        self.assertEqual(assistant.VOICE, "am_michael")
        self.assertEqual(assistant.SPEED, 1.2)
        self.assertEqual(assistant.CHUNK_SIZE, 300)

        # Ensure speech components were initialized
        self.assertTrue(mock_recognizer.called)
        self.assertTrue(mock_tts.called)

    @patch("anyrobo.speech.recognition.SpeechRecognizer")
    @patch("anyrobo.speech.synthesis.TextToSpeech")
    def test_custom_init(self, mock_tts: Any, mock_recognizer: Any) -> None:
        """Test initialization with custom parameters."""
        assistant: AnyRobo = AnyRobo(
            sample_rate=44100,
            silence_threshold=0.05,
            silence_duration=2.0,
            voice="custom_voice",
            speed=1.5,
            system_prompt="Custom prompt",
        )

        self.assertEqual(assistant.SAMPLE_RATE, 44100)
        self.assertEqual(assistant.SILENCE_THRESHOLD, 0.05)
        self.assertEqual(assistant.SILENCE_DURATION, 2.0)
        self.assertEqual(assistant.VOICE, "custom_voice")
        self.assertEqual(assistant.SPEED, 1.5)
        self.assertEqual(assistant.SYSTEM_PROMPT, "Custom prompt")


if __name__ == "__main__":
    unittest.main()
