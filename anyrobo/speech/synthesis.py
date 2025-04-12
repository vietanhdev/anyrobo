"""Text-to-speech synthesis functionality for AnyRobo."""

import os

import numpy as np

# Import the Kokoro class from kokoro_onnx
from kokoro_onnx import Kokoro

from anyrobo.models.loader import download_tts_model


class TextToSpeech:
    """Text-to-speech synthesis using Kokoro model."""

    def __init__(self, model_path: str = None, voices_path: str = None):
        """Initialize the text-to-speech engine.

        Args:
            model_path: Path to the Kokoro model file
            voices_path: Path to the voices file
        """
        # Find the model path
        if model_path is None:
            model_path = os.environ.get("ANYROBO_TTS_MODEL", None)
            if model_path is None:
                # Download the model if it doesn't exist
                model_path = download_tts_model()

        # Find the voices path
        if voices_path is None:
            voices_path = os.environ.get("ANYROBO_VOICES_PATH", None)
            if voices_path is None:
                # Use default voices file based on downloaded model
                voices_path = os.path.join(os.path.dirname(model_path), "voices-v1.0.bin")

        # Initialize Kokoro TTS
        self.kokoro = Kokoro(model_path, voices_path)

    def generate_audio(self, text: str, voice: str, speed: float) -> np.ndarray:
        """Convert text to speech audio.

        Args:
            text: Text to synthesize
            voice: Voice profile to use
            speed: Speed factor for speech

        Returns:
            Audio data as numpy array
        """
        if not text.strip():
            return np.array([], dtype=np.float32)

        # Use the kokoro library to generate audio with the simpler create method
        audio, sample_rate = self.kokoro.create(text, voice=voice, speed=speed, lang="en-us")

        return audio
