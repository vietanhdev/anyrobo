#!/usr/bin/env python3
"""
Voice-Enabled Assistant Example

This example demonstrates how to create a full voice-enabled assistant using
the AnyRobo framework with:
- STT (Speech-to-Text)
- LLM (Language Model)
- TTS (Text-to-Speech)

Features:
- Complete voice interaction loop (listen, understand, respond, repeat)
- Immediate continuous streaming of text to speech
- Control speech queue (pause, clear, resume)
- Toggle voice mode on/off
- Toggle listening mode on/off
"""

import argparse
import sys
import time
from typing import Any, Dict, Optional

import numpy as np

from anyrobo.brain.llm_handler import LLMHandler
from anyrobo.speech.tts_handler import TTSHandler
from anyrobo.speech.stt_handler import STTHandler
from anyrobo.utils.events import EventBus


class VoiceAssistant:
    """
    Voice-enabled assistant using STT, LLM, and TTS integration.

    This class demonstrates how to create a complete voice interaction loop:
    1. Listen for speech input using STT
    2. Process the input with an LLM
    3. Convert the response to speech using TTS
    4. Return to listening mode
    """

    def __init__(
        self,
        # LLM settings
        model_name: str = "llama3.2",
        system_prompt: Optional[str] = None,
        
        # TTS settings
        tts_voice: str = "af_heart",
        tts_speed: float = 1.5,
        tts_sample_rate: int = 16000,
        tts_chunk_size: int = 500,
        tts_max_queue_size: int = 20,
        tts_max_words_per_chunk: int = 10,
        
        # STT settings
        stt_model: str = "small",
        stt_silence_threshold: float = 0.01,
        stt_silence_duration: float = 1.0,
        
        # General settings
        debug: bool = True,
    ) -> None:
        """
        Initialize the voice assistant.

        Args:
            model_name: Name of the LLM model to use
            system_prompt: Optional system prompt for the LLM
            
            tts_voice: Voice ID to use for TTS
            tts_speed: Speech speed multiplier
            tts_sample_rate: Audio sample rate for TTS
            tts_chunk_size: Maximum size of text chunks (in characters)
            tts_max_queue_size: Maximum number of audio chunks to queue
            tts_max_words_per_chunk: Maximum words per TTS chunk
            
            stt_model: Speech recognition model to use
            stt_silence_threshold: Threshold for silence detection
            stt_silence_duration: Duration of silence to consider end of speech
            
            debug: Enable debug messages
        """
        # Enable debug printing
        self.debug = debug

        # Create the central event bus
        self.event_bus = EventBus()

        self._log("Creating LLM handler")
        # Create LLM handler
        self.llm = LLMHandler(
            model_name=model_name,
            system_prompt=system_prompt,
        )

        self._log("Creating TTS handler")
        # Create TTS handler
        self.tts = TTSHandler(
            voice=tts_voice,
            speed=tts_speed,
            sample_rate=tts_sample_rate,
            chunk_size=tts_chunk_size,
            max_queue_size=tts_max_queue_size,
            debug=debug,
        )
        
        self._log("Creating STT handler")
        # Create STT handler
        self.stt = STTHandler(
            model=stt_model,
            sample_rate=tts_sample_rate,  # Use same sample rate as TTS
            silence_threshold=stt_silence_threshold,
            silence_duration=stt_silence_duration,
        )

        # Override the default event bus for all handlers
        self._log("Setting custom event bus")
        self.llm._event_bus = self.event_bus
        self.tts._event_bus = self.event_bus
        self.stt._event_bus = self.event_bus

        # Register event handlers
        self._register_event_handlers()

        # Tracking variables
        self.current_response_id = ""
        self.llm_response_buffer = ""
        self.llm_is_generating = False

        # Model loading status
        self.llm_model_loaded = False
        self.tts_model_loaded = False
        self.stt_model_loaded = False

        # Mode flags
        self.voice_mode = True  # TTS enabled
        self.listening_mode = True  # STT enabled by default
        self.continuous_mode = True  # Continuous listening loop enabled by default
        
        # Statistics
        self.transcription_count = 0

    def _log(self, message: str) -> None:
        """Print debug message if debug is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def _register_event_handlers(self) -> None:
        """Register event handlers for LLM, TTS, and STT events."""
        self._log("Registering event handlers")
        
        # LLM events
        self.event_bus.subscribe(LLMHandler.MODEL_LOADED, self._on_llm_model_loaded)
        self.event_bus.subscribe(LLMHandler.RESPONSE_STARTED, self._on_llm_response_started)
        self.event_bus.subscribe(LLMHandler.RESPONSE_CHUNK, self._on_llm_response_chunk)
        self.event_bus.subscribe(LLMHandler.RESPONSE_COMPLETED, self._on_llm_response_completed)
        self.event_bus.subscribe(LLMHandler.RESPONSE_ERROR, self._on_llm_response_error)

        # TTS events
        self.event_bus.subscribe(TTSHandler.MODEL_LOADED, self._on_tts_model_loaded)
        self.event_bus.subscribe(TTSHandler.SPEECH_STARTED, self._on_speech_started)
        self.event_bus.subscribe(TTSHandler.SPEECH_ENDED, self._on_speech_ended)
        self.event_bus.subscribe(TTSHandler.SPEECH_CHUNK_STARTED, self._on_speech_chunk_started)
        self.event_bus.subscribe(TTSHandler.SPEECH_CHUNK_ENDED, self._on_speech_chunk_ended)
        self.event_bus.subscribe(TTSHandler.SPEECH_ERROR, self._on_speech_error)
        self.event_bus.subscribe(TTSHandler.SPEECH_PAUSED, self._on_speech_paused)
        self.event_bus.subscribe(TTSHandler.SPEECH_RESUMED, self._on_speech_resumed)
        
        # STT events
        self.event_bus.subscribe(STTHandler.LISTENING_STARTED, self._on_listening_started)
        self.event_bus.subscribe(STTHandler.LISTENING_STOPPED, self._on_listening_stopped)
        self.event_bus.subscribe(STTHandler.TRANSCRIPTION_STARTED, self._on_transcription_started)
        self.event_bus.subscribe(STTHandler.TRANSCRIPTION_RESULT, self._on_transcription_result)
        self.event_bus.subscribe(STTHandler.TRANSCRIPTION_ERROR, self._on_transcription_error)
        self.event_bus.subscribe("stt.audio.data", self._on_audio_data)

    def _on_llm_model_loaded(self, data: Dict[str, Any]) -> None:
        """Handle LLM model loaded event."""
        model = data.get("model", "unknown") if data else "unknown"
        print(f"[INFO] LLM model loaded successfully: {model}")
        self.llm_model_loaded = True

    def _on_tts_model_loaded(self, data: Dict[str, Any]) -> None:
        """Handle TTS model loaded event."""
        voice = data.get("voice", "unknown") if data else "unknown"
        print(f"[INFO] TTS model loaded successfully with voice {voice}")
        self.tts_model_loaded = True

    def _on_llm_response_started(self, data: Dict[str, Any]) -> None:
        """Handle LLM response started event."""
        response_id = data.get("response_id", "unknown") if data else "unknown"
        print(f"[INFO] LLM response generation started (ID: {response_id[:8]})")

        # Reset the buffer when starting a new response
        self.llm_response_buffer = ""
        self.llm_is_generating = True

    def _on_llm_response_chunk(self, data: Dict[str, Any]) -> None:
        """Handle LLM response chunk event."""
        response_id = data.get("response_id", "unknown") if data else "unknown"
        chunk = data.get("chunk", "") if data else ""

        # Print chunk without newline to show streaming
        print(chunk, end="", flush=True)

        # Accumulate chunks
        self.llm_response_buffer += chunk

        # If voice mode is enabled, stream the chunk directly to TTS
        if self.voice_mode and chunk:
            self.tts.stream_text(chunk)

    def _on_llm_response_completed(self, data: Dict[str, Any]) -> None:
        """Handle LLM response completed event."""
        response_id = data.get("response_id", "unknown") if data else "unknown"
        response = data.get("response", "") if data else ""

        print("\n\n[INFO] LLM response completed (ID: {})".format(response_id[:8]))
        self.llm_is_generating = False

        # Make sure we have the response in our buffer
        if not self.llm_response_buffer and response:
            self.llm_response_buffer = response

            # If voice mode is enabled, stream any remaining text
            if self.voice_mode and response:
                self.tts.stream_text(response)
                self.tts.flush()
        else:
            # Always flush any pending text when the response is complete
            if self.voice_mode:
                self.tts.flush()
        
        # If continuous mode is enabled, wait for TTS to finish then start listening again
        if self.continuous_mode:
            # Use the wait_until_done method to handle the waiting and restart
            self.wait_until_done()
            
            # Restart listening if continuous mode is enabled
            if self.continuous_mode and self.listening_mode:
                print("\n[INFO] Returning to listening mode...")
                self.stt.start_listening()

    def _on_llm_response_error(self, data: Dict[str, Any]) -> None:
        """Handle LLM response error event."""
        error = data.get("error", "Unknown error") if data else "Unknown error"
        print(f"[ERROR] LLM response error: {error}")
        self.llm_is_generating = False
        
        # Restart listening if continuous mode is enabled
        if self.continuous_mode and self.listening_mode:
            print("\n[INFO] Returning to listening mode after error...")
            self.stt.start_listening()

    def _on_speech_started(self, data: Any) -> None:
        """Handle speech started event."""
        print("\n[INFO] Speech playback started")

    def _on_speech_ended(self, data: Any) -> None:
        """Handle speech ended event."""
        canceled = data.get("canceled", False) if data else False

        if canceled:
            print(f"[INFO] Speech playback canceled")
        else:
            print(f"[INFO] Speech playback ended")
            
        # Restart listening if continuous mode is enabled and we're not already listening
        # This ensures we go back to listening after speech is done
        if self.continuous_mode and self.listening_mode and not self.stt.is_listening:
            print("\n[INFO] Returning to listening mode after speech ended...")
            self.stt.start_listening()

    def _on_speech_chunk_started(self, data: Dict[str, Any]) -> None:
        """Handle speech chunk started event."""
        chunk_num = data.get("chunk_num", 0) if data else 0
        self._log(f"Playing chunk {chunk_num}")

    def _on_speech_chunk_ended(self, data: Dict[str, Any]) -> None:
        """Handle speech chunk ended event."""
        chunk_num = data.get("chunk_num", 0) if data else 0
        self._log(f"Finished chunk {chunk_num}")

    def _on_speech_error(self, data: Dict[str, Any]) -> None:
        """Handle speech error event."""
        error = data.get("error", "Unknown error") if data else "Unknown error"
        print(f"[ERROR] Speech error: {error}")

    def _on_speech_paused(self, data: Any) -> None:
        """Handle speech paused event."""
        print("\n[INFO] Speech playback paused")

    def _on_speech_resumed(self, data: Any) -> None:
        """Handle speech resumed event."""
        print("\n[INFO] Speech playback resumed")
        
    def _on_listening_started(self, data: Any) -> None:
        """Handle listening started event."""
        print("\n[INFO] Listening started. Speak into your microphone...")

    def _on_listening_stopped(self, data: Any) -> None:
        """Handle listening stopped event."""
        print(f"\n[INFO] Listening stopped.")
        print(f"[INFO] Processed {self.transcription_count} transcriptions so far.")

    def _on_transcription_started(self, data: Any) -> None:
        """Handle transcription started event."""
        print("\n[INFO] Processing speech...")

    def _on_transcription_result(self, data: Dict[str, Any]) -> None:
        """Handle transcription result event."""
        self.transcription_count += 1
        text = data.get("text", "")
        
        if not text.strip():
            print("\n[INFO] Empty transcription detected.")
            
            # Restart listening if continuous mode is enabled
            if self.continuous_mode and self.listening_mode:
                print("[INFO] Returning to listening mode...")
                self.stt.start_listening()
            return
        
        print(f"\n[TRANSCRIPTION] {text}")

        # Stop listening while processing the transcription
        self.stt.stop_listening()
        
        # Send the transcribed text to the LLM
        self.generate_response(text)

    def _on_transcription_error(self, data: Dict[str, Any]) -> None:
        """Handle transcription error event."""
        error = data.get("error", "Unknown error")
        print(f"\n[ERROR] Transcription error: {error}")
        
        # Restart listening if continuous mode is enabled
        if self.continuous_mode and self.listening_mode:
            print("[INFO] Returning to listening mode after error...")
            self.stt.start_listening()

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

    def generate_response(self, user_message: str) -> None:
        """
        Generate a response to the given user message.

        Args:
            user_message: Message to send to the LLM
        """
        print(f"\n[USER] {user_message}")
        self.current_response_id = self.llm.generate_response(user_message)
        self._log(f"Response ID: {self.current_response_id}")

    def print_tts_status(self) -> None:
        """Print the current TTS status."""
        self.tts.print_status()

    def wait_for_model_loading(self, timeout: int = 10) -> bool:
        """
        Wait for all models to be loaded.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            bool: True if models were loaded, False if timed out
        """
        start_time = time.time()
        while (
            not self.llm_model_loaded or 
            not self.tts_model_loaded or
            not self.stt_model_loaded
        ) and time.time() - start_time < timeout:
            # Check LLM model
            if (
                not self.llm_model_loaded
                and hasattr(self.llm, "model_loaded")
                and self.llm.model_loaded
            ):
                self.llm_model_loaded = True
                print("LLM model loaded successfully")

            # Check TTS model
            if (
                not self.tts_model_loaded
                and hasattr(self.tts, "model_loaded")
                and self.tts.model_loaded
            ):
                self.tts_model_loaded = True
                print("TTS model loaded successfully")

            # Check STT model - assuming it has a similar attribute
            if (
                not self.stt_model_loaded
                and hasattr(self.stt, "model_loaded")
                and self.stt.model_loaded
            ):
                self.stt_model_loaded = True
                print("STT model loaded successfully")

            if not self.llm_model_loaded:
                print("Waiting for LLM model to load...")
                time.sleep(1)
            if not self.tts_model_loaded:
                print("Waiting for TTS model to load...")
                time.sleep(1)
            if not self.stt_model_loaded:
                print("Waiting for STT model to load...")
                time.sleep(1)

        return self.llm_model_loaded and self.tts_model_loaded and self.stt_model_loaded

    def toggle_voice_mode(self) -> None:
        """Toggle voice mode (TTS) on/off."""
        self.voice_mode = not self.voice_mode
        print(f"\n[INFO] Voice mode {'enabled' if self.voice_mode else 'disabled'}")
        
        # If disabling voice mode, clear any pending speech
        if not self.voice_mode:
            self.tts.clear()
    
    def toggle_listening_mode(self) -> None:
        """Toggle listening mode (STT) on/off."""
        self.listening_mode = not self.listening_mode
        
        if self.listening_mode:
            print(f"\n[INFO] Listening mode enabled. Starting to listen...")
            self.stt.start_listening()
        else:
            print(f"\n[INFO] Listening mode disabled. Stopping listening...")
            self.stt.stop_listening()
    
    def toggle_continuous_mode(self) -> None:
        """Toggle continuous interaction mode on/off."""
        self.continuous_mode = not self.continuous_mode
        print(f"\n[INFO] Continuous mode {'enabled' if self.continuous_mode else 'disabled'}")
        
        # If enabling continuous mode and listening is already on, make sure we're listening
        if self.continuous_mode and self.listening_mode and not self.stt.is_listening:
            self.stt.start_listening()

    def show_conversation_history(self) -> None:
        """Display the current conversation history."""
        print("\n----- Conversation History -----")
        for msg in self.llm.get_history():
            role = msg["role"].upper()
            content = msg["content"]
            print(f"[{role}] {content}")
        print("-------------------------------\n")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.tts.clear()
        self.stt.stop_listening()
        self.stt.cleanup()
        print("\n[INFO] Resources cleaned up.")

    def wait_until_done(self, timeout: float = 30.0) -> None:
        """
        Wait until both LLM and TTS processing are complete.
        
        This method blocks until:
        1. LLM has finished generating a response
        2. TTS has finished speaking all queued text
        3. All audio has been fully played through the output device
        
        Args:
            timeout: Maximum seconds to wait for TTS completion
        """
        # First, wait for LLM to finish generating response
        if self.llm_is_generating:
            print("[INFO] Waiting for LLM to complete response...")
            start_time = time.time()
            while self.llm_is_generating and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            if self.llm_is_generating:
                print("[WARN] Timed out waiting for LLM to complete")
                self.llm_is_generating = False
            else:
                print("[INFO] LLM processing complete")
                
        # Then wait for TTS to finish speaking
        if self.voice_mode:
            print("[INFO] Waiting for speech to complete...")
            # Use the new wait_until_done method that ensures all audio is fully played
            self.tts.wait_until_done(timeout=timeout)
            
        return


def main():
    """Run the voice-enabled assistant example."""
    parser = argparse.ArgumentParser(description="Voice-enabled assistant using AnyRobo framework")
    
    # LLM parameters
    parser.add_argument("--model", type=str, default="llama3.2", help="LLM model to use")
    parser.add_argument(
        "--system-prompt",
        type=str,
        default="You are a helpful AI assistant. Be concise.",
        help="System prompt for the LLM",
    )
    
    # TTS parameters
    parser.add_argument("--voice", type=str, default="af_heart", help="Voice ID to use for TTS")
    parser.add_argument("--speed", type=float, default=1.5, help="Speech speed multiplier")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Maximum size of text chunks in characters (default: 500)",
    )
    parser.add_argument(
        "--max-queue-size", type=int, default=20, help="Maximum audio queue size (default: 20)"
    )
    parser.add_argument(
        "--max-words", type=int, default=10, help="Maximum words per TTS chunk (default: 10)"
    )
    
    # STT parameters
    parser.add_argument(
        "--stt-model", type=str, default="small", 
        help="Speech recognition model (small, medium, large)"
    )
    parser.add_argument(
        "--silence-threshold", type=float, default=0.01, 
        help="Threshold for silence detection"
    )
    parser.add_argument(
        "--silence-duration", type=float, default=1.0,
        help="Duration of silence to consider end of speech (seconds)"
    )
    
    # Mode flags - all on by default, can be disabled
    parser.add_argument("--no-voice", action="store_true", help="Disable voice output")
    parser.add_argument("--no-listen", action="store_true", help="Disable listening mode")
    parser.add_argument("--no-continuous", action="store_true", help="Disable continuous interaction mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()

    # Create the assistant instance
    assistant = VoiceAssistant(
        # LLM settings
        model_name=args.model,
        system_prompt=args.system_prompt,
        
        # TTS settings
        tts_voice=args.voice,
        tts_speed=args.speed,
        tts_chunk_size=args.chunk_size,
        tts_max_queue_size=args.max_queue_size,
        tts_max_words_per_chunk=args.max_words,
        
        # STT settings
        stt_model=args.stt_model,
        stt_silence_threshold=args.silence_threshold,
        stt_silence_duration=args.silence_duration,
        
        # General settings
        debug=args.debug,
    )

    # Apply mode flags if provided
    if args.no_voice:
        assistant.toggle_voice_mode()  # Turn off voice mode
    
    if args.no_continuous:
        assistant.toggle_continuous_mode()  # Turn off continuous mode
        
    if args.no_listen:
        assistant.toggle_listening_mode()  # Turn off listening mode

    # Wait for models to load
    if not assistant.wait_for_model_loading():
        print("Model loading timed out. Make sure required services are running.")
        return

    print("\nVoice-Enabled Assistant running in continuous mode.")
    print("Press Ctrl+C to stop the program.")
    
    # Start listening
    if assistant.listening_mode and not assistant.stt.is_listening:
        assistant.stt.start_listening()

    try:
        # Simple loop that just keeps the program running
        # All interaction is handled by event handlers
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user")
    finally:
        # Cleanup
        assistant.cleanup()
        print("Voice-Enabled Assistant stopped.")


if __name__ == "__main__":
    main()
