"""
Speech-to-Text Handler for the AnyRobo framework.

Handles audio input and speech recognition.
"""

import threading
import time

import numpy as np
import sounddevice as sd

from anyrobo.speech.recognition import SpeechRecognizer
from anyrobo.utils.events import Component


class STTHandler(Component):
    """
    Handles speech-to-text recognition and audio input.

    Listens to audio input, detects speech, and transcribes it using
    a speech recognition model.
    """

    # Event topics
    LISTENING_STARTED = "stt.listening.started"
    LISTENING_STOPPED = "stt.listening.stopped"
    LISTENING_PAUSED = "stt.listening.paused"
    LISTENING_RESUMED = "stt.listening.resumed"
    TRANSCRIPTION_STARTED = "stt.transcription.started"
    TRANSCRIPTION_RESULT = "stt.transcription.result"
    TRANSCRIPTION_ERROR = "stt.transcription.error"

    def __init__(
        self,
        model: str = "small",
        sample_rate: int = 16000,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.0,
    ) -> None:
        """
        Initialize the STT handler.

        Args:
            model: Speech recognition model to use
            sample_rate: Audio sample rate
            silence_threshold: Threshold for silence detection
            silence_duration: Duration of silence to consider end of speech
        """
        super().__init__()

        # Configuration
        self.model = model
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration

        # State variables
        self.is_listening = False
        self.is_listening_paused = False
        self.audio_buffer = []
        self.silence_frames = 0
        self.audio_data_being_captured = False

        # Initialize speech recognizer
        self.speech_recognizer = SpeechRecognizer(model=self.model, batch_size=12)
        self.model_loaded = True

        # Audio stream
        self.stream = None

        # Processing flag to prevent multiple simultaneous processing
        self.is_processing = False
        self.processing_lock = threading.Lock()

    def start_listening(self) -> bool:
        """
        Start listening for voice input.

        Returns:
            bool: True if listening started successfully, False otherwise
        """
        if self.is_listening:
            return False

        self.is_listening = True
        self.is_listening_paused = False

        # Reset audio buffer and counters
        self.audio_buffer = []
        self.silence_frames = 0

        # Publish event
        self.publish_event(self.LISTENING_STARTED, None)

        # Start audio stream in a separate thread
        threading.Thread(target=self._listen_for_audio, daemon=True).start()

        return True

    def pause_listening(self) -> bool:
        """
        Temporarily pause audio input.

        Returns:
            bool: True if listening was paused, False otherwise
        """
        if not self.is_listening or self.is_listening_paused:
            return False

        self.is_listening_paused = True

        # Publish event
        self.publish_event(self.LISTENING_PAUSED, None)

        return True

    def resume_listening(self) -> bool:
        """
        Resume audio input if it was paused.

        Returns:
            bool: True if listening was resumed, False otherwise
        """
        if not self.is_listening or not self.is_listening_paused:
            return False

        self.is_listening_paused = False

        # Publish event
        self.publish_event(self.LISTENING_RESUMED, None)

        return True

    def stop_listening(self) -> bool:
        """
        Stop listening for voice input.

        Returns:
            bool: True if listening was stopped, False otherwise
        """
        if not self.is_listening:
            return False

        self.is_listening = False

        # Close stream if active
        if self.stream is not None:
            try:
                self.stream.close()
                self.stream = None
            except Exception as e:
                print(f"Error closing audio stream: {e}")

        # Publish event
        self.publish_event(self.LISTENING_STOPPED, None)

        return True

    def is_active(self) -> bool:
        """
        Check if STT is actively listening.

        Returns:
            bool: True if listening and not paused, False otherwise
        """
        return self.is_listening and not self.is_listening_paused

    def _listen_for_audio(self) -> None:
        """Listen for audio input and process it."""
        try:
            # Tracking variables for better silence detection
            self.audio_data_being_captured = False
            last_active_time = time.time()
            min_recording_time = 1.0  # Minimum recording time in seconds

            def audio_callback(
                indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
            ) -> None:
                """Callback for audio stream."""
                nonlocal last_active_time

                if not self.is_listening:
                    raise sd.CallbackStop

                # Skip processing if listening is paused
                if self.is_listening_paused:
                    return

                if status:
                    print(f"Audio status: {status}")

                # Get audio data and calculate volume level
                audio = indata.flatten()
                level = np.abs(audio).mean()

                # Publish audio data for visualization
                self.publish_event("stt.audio.data", {"audio_data": audio})

                # Add to buffer (always capture data)
                self.audio_buffer.extend(audio.tolist())

                # Detect speech activity
                if level >= self.silence_threshold:
                    # Active speech detected
                    self.audio_data_being_captured = True
                    last_active_time = time.time()
                    self.silence_frames = 0
                else:
                    # Count silent frames only if we're recording
                    if self.audio_data_being_captured:
                        self.silence_frames += len(audio)

                # Process audio when we detect silence after speech
                if (
                    self.audio_data_being_captured
                    and self.silence_frames > self.silence_duration * self.sample_rate
                    and len(self.audio_buffer) > self.sample_rate * min_recording_time
                ):
                    # Create a copy to avoid race conditions
                    audio_segment = np.array(self.audio_buffer, dtype=np.float32)

                    # Process the audio
                    threading.Thread(
                        target=self._process_audio, args=(audio_segment,), daemon=True
                    ).start()

                    # Reset state
                    self.audio_buffer = []
                    self.silence_frames = 0
                    self.audio_data_being_captured = False

            # Start audio stream
            with sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                dtype=np.float32,
                blocksize=int(0.05 * self.sample_rate),  # 50ms blocks for responsiveness
            ) as stream:
                self.stream = stream

                # Keep running until stopped
                while self.is_listening:
                    sd.sleep(100)

        except Exception as e:
            print(f"Error in audio listening: {e}")

            if self.is_listening:
                self.stop_listening()
                # Publish error event
                self.publish_event(self.TRANSCRIPTION_ERROR, {"error": str(e)})

    def _process_audio(self, audio_segment: np.ndarray) -> None:
        """
        Process recorded audio segment.

        Args:
            audio_segment: Audio data as numpy array
        """
        # Skip if not listening or paused
        if not self.is_listening or self.is_listening_paused:
            return

        # Use a lock to prevent multiple processing at the same time
        with self.processing_lock:
            if self.is_processing:
                print("Already processing audio, skipping...")
                return

            self.is_processing = True

        try:
            # Publish transcription started event
            self.publish_event(self.TRANSCRIPTION_STARTED, None)

            # Transcribe audio
            result = self.speech_recognizer.transcribe(audio_segment)
            text = result.get("text", "").strip()

            # Only publish non-empty transcriptions
            if text:
                # Publish transcription result
                self.publish_event(
                    self.TRANSCRIPTION_RESULT,
                    {"text": text, "confidence": result.get("confidence", 0.0)},
                )

        except Exception as e:
            print(f"Error processing audio: {e}")
            # Publish error event
            self.publish_event(self.TRANSCRIPTION_ERROR, {"error": str(e)})

        finally:
            # Reset processing flag
            self.is_processing = False

    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        # Stop listening if active
        if self.is_listening:
            self.stop_listening()

        # Clean up parent resources
        super().cleanup()
