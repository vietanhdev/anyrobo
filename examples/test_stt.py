#!/usr/bin/env python3
"""
Speech Recognition Test Example

This example demonstrates how to use the STTHandler to perform speech-to-text
recognition using the AnyRobo framework.
"""

import argparse
import sys
import time
from typing import Any, Dict, Optional

import numpy as np

from anyrobo.speech.stt_handler import STTHandler
from anyrobo.utils.events import EventBus


class SpeechRecognitionTest:
    """
    Test class for speech recognition using the STTHandler.

    This class demonstrates how to use the STTHandler to capture audio
    and transcribe speech in real-time.
    """

    def __init__(
        self,
        model: str = "small",
        sample_rate: int = 16000,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.0,
        max_test_duration: int = 60,
    ) -> None:
        """
        Initialize the speech recognition test.

        Args:
            model: Speech recognition model to use
            sample_rate: Audio sample rate
            silence_threshold: Threshold for silence detection
            silence_duration: Duration of silence to consider end of speech
            max_test_duration: Maximum duration of the test in seconds
        """
        # Create the central event bus
        self.event_bus = EventBus()

        # Create STT handler
        self.stt = STTHandler(
            model=model,
            sample_rate=sample_rate,
            silence_threshold=silence_threshold,
            silence_duration=silence_duration,
        )

        # Override the default event bus in STTHandler
        self.stt._event_bus = self.event_bus

        # Register event handlers
        self._register_event_handlers()

        # Configuration
        self.max_test_duration = max_test_duration

        # Statistics
        self.transcription_count = 0
        self.start_time: Optional[float] = None

    def _register_event_handlers(self) -> None:
        """Register event handlers for STT events."""
        self.event_bus.subscribe(STTHandler.LISTENING_STARTED, self._on_listening_started)
        self.event_bus.subscribe(STTHandler.LISTENING_STOPPED, self._on_listening_stopped)
        self.event_bus.subscribe(STTHandler.TRANSCRIPTION_STARTED, self._on_transcription_started)
        self.event_bus.subscribe(STTHandler.TRANSCRIPTION_RESULT, self._on_transcription_result)
        self.event_bus.subscribe(STTHandler.TRANSCRIPTION_ERROR, self._on_transcription_error)
        self.event_bus.subscribe("stt.audio.data", self._on_audio_data)

    def _on_listening_started(self, data: Any) -> None:
        """Handle listening started event."""
        print("\n[INFO] Listening started. Speak into your microphone...")
        self.start_time = time.time()

    def _on_listening_stopped(self, data: Any) -> None:
        """Handle listening stopped event."""
        duration = time.time() - (self.start_time or 0)
        print(f"\n[INFO] Listening stopped after {duration:.2f} seconds.")
        print(f"[INFO] Processed {self.transcription_count} transcriptions.")

    def _on_transcription_started(self, data: Any) -> None:
        """Handle transcription started event."""
        print("\n[INFO] Processing speech...")

    def _on_transcription_result(self, data: Dict[str, Any]) -> None:
        """Handle transcription result event."""
        self.transcription_count += 1
        text = data.get("text", "")
        print(f"\n[TRANSCRIPTION] {text}")

        # Additional information if available
        if "segments" in data:
            print(f"[INFO] Detected {len(data['segments'])} speech segments")

        # Print elapsed time
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"[INFO] Elapsed time: {elapsed:.2f} seconds")

    def _on_transcription_error(self, data: Dict[str, Any]) -> None:
        """Handle transcription error event."""
        error = data.get("error", "Unknown error")
        print(f"\n[ERROR] Transcription error: {error}")

    def _on_audio_data(self, data: Dict[str, Any]) -> None:
        """Handle audio data event (for visualization or level monitoring)."""
        audio_data = data.get("audio_data", np.array([]))
        if len(audio_data) > 0:
            # Calculate audio level for simple visualization
            level = np.abs(audio_data).mean()
            self._visualize_audio_level(level)

    def _visualize_audio_level(self, level: float) -> None:
        """Visualize audio level as a simple ASCII bar."""
        # Scale the level to 0-50 for display
        scaled_level = min(int(level * 500), 50)
        # Overwrite the line with a new visualization
        bar = "█" * scaled_level
        sys.stdout.write(f"\r[LEVEL] {bar.ljust(50)} {level:.4f}")
        sys.stdout.flush()

    def run(self) -> None:
        """Run the speech recognition test."""
        try:
            print("Starting Speech Recognition Test")
            print("=" * 50)
            print("Model: ", self.stt.model)
            print("Sample Rate: ", self.stt.sample_rate)
            print("Silence Threshold: ", self.stt.silence_threshold)
            print("Silence Duration: ", self.stt.silence_duration)
            print("=" * 50)
            print("Press Ctrl+C to stop the test at any time")

            # Start listening for audio
            self.stt.start_listening()

            # Run for specified duration or until interrupted
            end_time = time.time() + self.max_test_duration
            while time.time() < end_time:
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
        finally:
            # Cleanup
            self.stt.stop_listening()
            self.stt.cleanup()
            print("\nSpeech Recognition Test completed.")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test speech recognition using AnyRobo")
    parser.add_argument(
        "--model", type=str, default="small", help="Speech recognition model (small, medium, large)"
    )
    parser.add_argument("--sample-rate", type=int, default=16000, help="Audio sample rate")
    parser.add_argument(
        "--silence-threshold", type=float, default=0.01, help="Threshold for silence detection"
    )
    parser.add_argument(
        "--silence-duration",
        type=float,
        default=1.0,
        help="Duration of silence to consider end of speech (seconds)",
    )
    parser.add_argument("--duration", type=int, default=60, help="Maximum test duration in seconds")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    test = SpeechRecognitionTest(
        model=args.model,
        sample_rate=args.sample_rate,
        silence_threshold=args.silence_threshold,
        silence_duration=args.silence_duration,
        max_test_duration=args.duration,
    )

    test.run()
