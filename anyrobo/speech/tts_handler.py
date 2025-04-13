"""
Text-to-Speech Handler for the AnyRobo framework.

Handles text-to-speech processing and audio playback.
"""

import queue
import re
import threading
import time
from typing import List, Optional

import numpy as np
import sounddevice as sd

from anyrobo.models.loader import download_tts_model
from anyrobo.speech.synthesis import TextToSpeech
from anyrobo.utils.events import Component


class TTSHandler(Component):
    """
    Simplified Text-to-Speech handler with a single session.
    
    Converts text to spoken audio with a streamlined interface:
    - stream_text: Add text to the speech queue
    - flush: Process all pending text immediately
    - clear: Clear all pending speech
    - stop: Stop current playback
    - pause: Pause playback
    - start: Resume playback
    """

    # Event topics
    SPEECH_STARTED = "tts.speech.started"
    SPEECH_ENDED = "tts.speech.ended"
    SPEECH_CHUNK_STARTED = "tts.speech.chunk.started"
    SPEECH_CHUNK_ENDED = "tts.speech.chunk.ended"
    SPEECH_ERROR = "tts.speech.error"
    MODEL_LOADED = "tts.model.loaded"
    SPEECH_PAUSED = "tts.speech.paused"
    SPEECH_RESUMED = "tts.speech.resumed"

    def __init__(
        self,
        voice: str = "af_heart",
        speed: float = 1.5,
        sample_rate: int = 16000,
        chunk_size: int = 500,
        max_queue_size: int = 20,
        min_chunk_size: int = 15,
        debug: bool = False,
    ) -> None:
        """
        Initialize the simplified TTS handler.

        Args:
            voice: Voice ID to use
            speed: Speech speed
            sample_rate: Audio sample rate
            chunk_size: Maximum size of text chunks (in characters)
            max_queue_size: Maximum number of audio chunks to queue
            min_chunk_size: Minimum number of words required to process a chunk (default: 1)
            debug: Enable debug printing (default: False)
        """
        super().__init__()

        # Configuration
        self.voice = voice
        self.speed = speed
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.max_queue_size = max_queue_size
        self.min_chunk_size = min_chunk_size
        self.debug = debug

        # Text buffer last update time
        self.buffer_last_update = time.time()

        # Initialize TTS component
        self.tts = TextToSpeech()

        # Audio queue and state
        self.audio_queue = queue.Queue(maxsize=max_queue_size)
        self.is_playing = False
        self.is_paused = False
        
        # Text streaming buffer
        self.text_buffer = ""
        self.text_buffer_lock = threading.Lock()
        
        # Debug tracking
        self.current_processing_text = ""
        self.current_playing_audio_length = 0
        self.missed_text = []
        self.total_text_received = 0
        self.total_text_processed = 0
        self.total_audio_played = 0

        # Sentence boundary pattern for text splitting
        self.sentence_pattern = re.compile(r"([.!?])\s+|([.!?])$")

        # Threading
        self.active = True
        self.tts_executor = threading.Thread(target=self._text_processor, daemon=True)
        self.player_thread = threading.Thread(target=self._audio_player, daemon=True)
        
        # State controlling events
        self.playback_completed = threading.Event()
        self.playback_completed.set()  # Initially set as completed
        
        # Model loading status
        self.model_loaded = False

        # Start threads
        self.tts_executor.start()
        self.player_thread.start()

        # Try to load TTS model in the background
        threading.Thread(target=self._load_model, daemon=True).start()

    def _load_model(self) -> None:
        """Load TTS model in the background."""
        try:
            download_tts_model()
            self.model_loaded = True
            self.publish_event(self.MODEL_LOADED, {"voice": self.voice})

            # Test the sound device after model loading
            test_data = np.zeros(1000, dtype=np.float32)
            sd.play(test_data, self.sample_rate, blocking=False)
            
            print("TTS model loaded successfully")
        except Exception as e:
            print(f"Error loading TTS model: {e}")
            self.publish_event(self.SPEECH_ERROR, {"error": f"Failed to load TTS model: {e}"})

    def _audio_player(self) -> None:
        """Background thread that plays TTS audio."""
        while self.active:
            try:
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                    
                try:
                    # Try to get the next audio chunk (non-blocking)
                    audio_data = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    # If queue is empty, just loop and check again
                    self.is_playing = False
                    self.playback_completed.set()
                    time.sleep(0.1)
                    continue

                # Set playing flag
                self.is_playing = True
                self.playback_completed.clear()
                
                # Track audio length for debugging
                self.current_playing_audio_length = len(audio_data) if audio_data is not None else 0
                
                # Publish event before playing
                self.publish_event(self.SPEECH_CHUNK_STARTED, {"chunk_num": 1})
                
                # Play the audio
                if self.debug:
                    print(f"[TTS DEBUG] Playing audio chunk with {self.current_playing_audio_length} samples")
                
                sd.play(audio_data, self.sample_rate, blocking=True)
                sd.wait()
                
                # Update metrics
                self.total_audio_played += 1
                
                # Mark task as done
                self.audio_queue.task_done()
                
                # Publish event after playing
                self.publish_event(self.SPEECH_CHUNK_ENDED, {"chunk_num": 1})
                
                # If queue is now empty, mark as completed
                if self.audio_queue.empty():
                    # Process any remaining text in the buffer
                    with self.text_buffer_lock:
                        if self.text_buffer:
                            # If there's still text in the buffer, flush it
                            if self.debug:
                                print(f"[TTS DEBUG] Processing remaining text in buffer: '{self.text_buffer}'")
                            text = self.text_buffer
                            self.text_buffer = ""
                            self.text_buffer_lock.release()
                            self.flush_text(text)
                            self.text_buffer_lock.acquire()
                    
                    # If queue is still empty after flushing
                    if self.audio_queue.empty():
                        self.is_playing = False
                        self.playback_completed.set()
                        self.publish_event(self.SPEECH_ENDED, {})
                
            except Exception as e:
                print(f"Error in audio player thread: {e}")
                self.publish_event(self.SPEECH_ERROR, {"error": f"Audio playback error: {e}"})
                time.sleep(0.1)  # Avoid spinning if there's a persistent error

    def _text_processor(self) -> None:
        """Process text buffer in the background."""
        while self.active:
            try:
                # Check if there's text to process
                with self.text_buffer_lock:
                    if not self.text_buffer:
                        time.sleep(0.1)
                        continue
                        
                    # Check if we should process the buffer
                    word_count = len(self.text_buffer.split())
                    
                    # Process the buffer if:
                    # 1. The buffer has more than min_chunk_size words
                    # 2. The buffer contains sentence-ending punctuation
                    has_punctuation = any(p in self.text_buffer for p in [".", "!", "?"])
                    should_process = (
                        word_count >= self.min_chunk_size
                        or has_punctuation
                    )
                    
                    if not should_process:
                        time.sleep(0.05)  # Short sleep time for better responsiveness
                        continue
                        
                    # Process the buffer
                    text_to_process = self.text_buffer
                    self.text_buffer = ""
                    self.current_processing_text = text_to_process  # For debugging
                
                # Generate audio for the text
                try:
                    if self.debug:
                        print(f"[TTS DEBUG] Processing text: '{text_to_process}'")
                    
                    self.total_text_processed += len(text_to_process)
                    audio_data = self.tts.generate_audio(text_to_process, self.voice, self.speed)
                    
                    # Skip empty audio
                    if audio_data is None or len(audio_data) <= 0:
                        if self.debug:
                            print(f"[TTS DEBUG] Warning: Empty audio generated for: '{text_to_process}'")
                            self.missed_text.append(text_to_process)
                        continue
                        
                    # Put audio in the queue
                    self.audio_queue.put(audio_data)
                    
                    # If this is the first chunk, publish started event
                    if not self.is_playing and not self.is_paused:
                        self.publish_event(self.SPEECH_STARTED, {})
                        
                except Exception as e:
                    print(f"Error generating audio: {e}")
                    self.publish_event(self.SPEECH_ERROR, {"error": f"Audio generation error: {e}"})
                    
            except Exception as e:
                print(f"Error in text processor thread: {e}")
                time.sleep(0.1)

    def _split_into_chunks(self, text: str, max_length: int) -> List[str]:
        """
        Split text into manageable chunks for TTS processing.
        
        Args:
            text: Text to split
            max_length: Maximum character length for each chunk
            
        Returns:
            List of text chunks
        """
        # If text is short enough, return as a single chunk
        if len(text) <= max_length:
            return [text]
            
        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_len = len(word) + 1  # +1 for the space
            
            if current_length + word_len > max_length:
                # Chunk is full, add it to results
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_len
            else:
                # Add word to current chunk
                current_chunk.append(word)
                current_length += word_len
                
        # Add any remaining words
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    # Public API - Main actions

    def stream_text(self, text: str) -> None:
        """
        Stream text to be spoken.
        
        Args:
            text: Text to be converted to speech
        """
        if not text:
            return
        
        self.total_text_received += len(text)
            
        with self.text_buffer_lock:
            self.text_buffer += text
            self.buffer_last_update = time.time()
            
        if self.debug:
            print(f"[TTS DEBUG] Added to buffer: '{text}'")
            print(f"[TTS DEBUG] Current buffer: '{self.text_buffer}'")

    def flush_text(self, text: str) -> None:
        """
        Process the given text immediately.
        
        Args:
            text: Text to process immediately
        """
        if not text:
            return
            
        # Split into manageable chunks
        chunks = self._split_into_chunks(text, self.chunk_size)
        
        # Generate audio for each chunk
        for chunk in chunks:
            try:
                if self.debug:
                    print(f"[TTS DEBUG] Generating audio for: '{chunk}'")
                    
                audio_data = self.tts.generate_audio(chunk, self.voice, self.speed)
                if audio_data is not None and len(audio_data) > 0:
                    self.audio_queue.put(audio_data)
                    
                    # If this is the first chunk, publish started event
                    if not self.is_playing and not self.is_paused:
                        self.publish_event(self.SPEECH_STARTED, {})
                else:
                    if self.debug:
                        print(f"[TTS DEBUG] Warning: Empty audio generated for: '{chunk}'")
                        self.missed_text.append(chunk)
            except Exception as e:
                print(f"Error generating audio during flush: {e}")
                self.publish_event(self.SPEECH_ERROR, {"error": f"Audio generation error: {e}"})

    def flush(self) -> None:
        """
        Process all pending text in the buffer immediately.
        """
        with self.text_buffer_lock:
            if not self.text_buffer:
                return
                
            # Process text in chunks if needed
            text = self.text_buffer
            self.text_buffer = ""
            
        # Process the text
        self.flush_text(text)

    def clear(self) -> None:
        """
        Clear all pending text and audio.
        """
        # Clear the text buffer
        with self.text_buffer_lock:
            self.text_buffer = ""
            
        # Stop any currently playing audio
        self.stop()
        
        # Clear the audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break
                
        self.publish_event(self.SPEECH_ENDED, {"canceled": True})

    def stop(self) -> None:
        """
        Stop current playback immediately.
        """
        try:
            sd.stop()
            self.is_playing = False
            self.playback_completed.set()
        except Exception as e:
            print(f"Error stopping audio: {e}")
            self.publish_event(self.SPEECH_ERROR, {"error": f"Stop error: {e}"})

    def pause(self) -> None:
        """
        Pause audio playback.
        """
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            try:
                sd.stop()
                self.publish_event(self.SPEECH_PAUSED, {})
            except Exception as e:
                print(f"Error pausing audio: {e}")
                self.publish_event(self.SPEECH_ERROR, {"error": f"Pause error: {e}"})

    def start(self) -> None:
        """
        Resume paused playback.
        """
        if self.is_paused:
            self.is_paused = False
            self.publish_event(self.SPEECH_RESUMED, {})

    def wait_for_completion(self, timeout: float = None) -> bool:
        """
        Wait for all queued speech to complete.
        
        Args:
            timeout: Maximum time to wait in seconds, or None to wait indefinitely
            
        Returns:
            bool: True if speech completed, False if timeout
        """
        return self.playback_completed.wait(timeout=timeout)
        
    def wait_until_done(self, timeout: float = None) -> bool:
        """
        Wait until all text has been processed and all audio has been fully played.
        
        This is a more comprehensive wait than wait_for_completion as it ensures:
        1. Any buffered text has been processed
        2. All audio has been generated
        3. All audio has been played through the output device
        
        Args:
            timeout: Maximum time to wait in seconds, or None to wait indefinitely
            
        Returns:
            bool: True if all processing and playback completed, False if timeout
        """
        start_time = time.time()
        
        # First, flush any text in the buffer to ensure it gets processed
        self.flush()
        
        # Check if we have a timeout and how much time is left
        time_left = None
        if timeout is not None:
            time_left = timeout - (time.time() - start_time)
            if time_left <= 0:
                return False
        
        # Wait for the playback to complete
        result = self.playback_completed.wait(timeout=time_left)
        
        # If playback is reported as complete, double-check actual audio device status
        if result:
            # Short extra wait to ensure the sound device has actually finished
            # This covers cases where the sounddevice module's internal state
            # might not be perfectly synchronized with our event flag
            try:
                status = sd.get_status()
                if status.active:
                    # If still active, wait a bit longer
                    time.sleep(0.2)
                    # Check again
                    status = sd.get_status()
                    if status.active and timeout is not None:
                        time_left = timeout - (time.time() - start_time)
                        if time_left > 0:
                            time.sleep(min(0.5, time_left))
            except Exception as e:
                # If we can't check status, just do a small wait to be safe
                time.sleep(0.1)
        
        # Return the final result
        return result

    def is_speaking(self) -> bool:
        """
        Check if TTS is currently playing audio.
        
        Returns:
            bool: True if speaking, False otherwise
        """
        return self.is_playing and not self.is_paused
        
    def print_status(self) -> None:
        """
        Print the current status of the TTS handler for debugging.
        """
        print("\n--- TTS Status ---")
        print(f"Is playing: {self.is_playing}")
        print(f"Is paused: {self.is_paused}")
        print(f"Buffer content: '{self.text_buffer}'")
        print(f"Buffer last updated: {time.time() - self.buffer_last_update:.2f}s ago")
        print(f"Current processing: '{self.current_processing_text}'")
        print(f"Audio queue size: {self.audio_queue.qsize()}/{self.max_queue_size}")
        print(f"Total text received: {self.total_text_received} chars")
        print(f"Total text processed: {self.total_text_processed} chars")
        print(f"Total audio chunks played: {self.total_audio_played}")
        if self.missed_text:
            print(f"Missed text ({len(self.missed_text)} chunks):")
            for i, text in enumerate(self.missed_text[-5:]):  # Show last 5 missed chunks
                print(f"  {i+1}. '{text}'")
        print("------------------\n")

    def cleanup(self) -> None:
        """
        Clean up resources before shutting down.
        """
        self.active = False
        self.clear()
        time.sleep(0.5)  # Give threads time to shut down
