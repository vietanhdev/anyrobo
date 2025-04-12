"""Speech recognition functionality for AnyRobo."""

from typing import Any, Dict

import numpy as np
from lightning_whisper_mlx import LightningWhisperMLX


class SpeechRecognizer:
    """Speech recognition using Whisper MLX."""

    def __init__(self, model: str = "small", batch_size: int = 12):
        """Initialize the speech recognizer.

        Args:
            model: Whisper model size (small, medium, large)
            batch_size: Batch size for processing
        """
        self.whisper_sample_rate = 16000
        self.whisper_mlx = LightningWhisperMLX(model=model, batch_size=batch_size)

    def transcribe(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Transcribe speech from audio data.

        Args:
            audio_data: Audio data as numpy array

        Returns:
            Dictionary with 'text' key containing the transcription
        """
        return self.whisper_mlx.transcribe(audio_data)
