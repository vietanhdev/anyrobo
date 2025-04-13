#!/usr/bin/env python3
"""
LLM and TTS Integration Example

This example demonstrates how to use the LLMHandler with TTSHandler to create
a voice-enabled conversational AI using the AnyRobo framework.

Features:
- Integrate LLM text generation with Text-to-Speech
- Immediate continuous streaming of text to speech
- Control speech queue (pause, clear, resume)
- Toggle voice mode on/off
"""

import argparse
import time
from typing import Any, Dict, Optional

from anyrobo.brain.llm_handler import LLMHandler
from anyrobo.speech.tts_handler import TTSHandler
from anyrobo.utils.events import EventBus


class LLMTTSTest:
    """
    Test class for integrating LLM and TTS capabilities.

    This class demonstrates how to initialize LLM and TTS handlers,
    send messages to the LLM, and convert the responses to speech.

    Features:
    - Immediate continuous streaming of text-to-speech for LLM outputs
    - Direct text streaming to TTS via `stream_text`
    - Queue management for TTS playback
    """

    def __init__(
        self,
        model_name: str = "llama3.2",
        system_prompt: Optional[str] = None,
        voice: str = "af_heart",
        speed: float = 1.5,
        sample_rate: int = 16000,
        chunk_size: int = 500,
        max_queue_size: int = 20,
        max_words_per_chunk: int = 10,
        debug: bool = True,
    ) -> None:
        """
        Initialize the LLM and TTS test.

        Args:
            model_name: Name of the LLM model to use
            system_prompt: Optional system prompt for the LLM
            voice: Voice ID to use for TTS
            speed: Speech speed multiplier
            sample_rate: Audio sample rate
            chunk_size: Maximum size of text chunks (in characters)
            max_queue_size: Maximum number of audio chunks to queue
            max_words_per_chunk: Maximum words per TTS chunk
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
            voice=voice,
            speed=speed,
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            max_queue_size=max_queue_size,
            debug=debug,  # Pass debug flag to TTS handler
        )

        # Override the default event bus for both handlers
        self._log("Setting custom event bus")
        self.llm._event_bus = self.event_bus
        self.tts._event_bus = self.event_bus

        # Register event handlers
        self._register_event_handlers()

        # Tracking variables
        self.current_response_id = ""
        self.llm_response_buffer = ""

        # Model loading status
        self.llm_model_loaded = False
        self.tts_model_loaded = False

        # Voice mode flag - always enabled by default
        self.voice_mode = True

    def _log(self, message: str) -> None:
        """Print debug message if debug is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def _register_event_handlers(self) -> None:
        """Register event handlers for LLM and TTS events."""
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

    def _on_llm_response_error(self, data: Dict[str, Any]) -> None:
        """Handle LLM response error event."""
        error = data.get("error", "Unknown error") if data else "Unknown error"
        print(f"[ERROR] LLM response error: {error}")

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
        Wait for the LLM and TTS models to be loaded.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            bool: True if models were loaded, False if timed out
        """
        start_time = time.time()
        while (
            not self.llm_model_loaded or not self.tts_model_loaded
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

            if not self.llm_model_loaded:
                print("Waiting for LLM model to load...")
                time.sleep(1)
            if not self.tts_model_loaded:
                print("Waiting for TTS model to load...")
                time.sleep(1)

        return self.llm_model_loaded and self.tts_model_loaded

    def toggle_voice_mode(self) -> None:
        """Toggle voice mode on/off."""
        self.voice_mode = not self.voice_mode
        print(f"\n[INFO] Voice mode {'enabled' if self.voice_mode else 'disabled'}")
        
        # If disabling voice mode, clear any pending speech
        if not self.voice_mode:
            self.tts.clear()

    def show_conversation_history(self) -> None:
        """Display the current conversation history."""
        print("\n----- Conversation History -----")
        for msg in self.llm.get_history():
            role = msg["role"].upper()
            content = msg["content"]
            print(f"[{role}] {content}")
        print("-------------------------------\n")


def main():
    """Run the LLM and TTS integration example."""
    parser = argparse.ArgumentParser(description="Test the AnyRobo LLM and TTS integration")
    parser.add_argument("--model", type=str, default="llama3.2", help="LLM model to use")
    parser.add_argument(
        "--system-prompt",
        type=str,
        default="You are a helpful AI assistant. Be concise.",
        help="System prompt for the LLM",
    )
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
    parser.add_argument("--no-voice", action="store_true", help="Start with voice mode disabled")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()

    # Create the test instance
    test = LLMTTSTest(
        model_name=args.model,
        system_prompt=args.system_prompt,
        voice=args.voice,
        speed=args.speed,
        chunk_size=args.chunk_size,
        max_queue_size=args.max_queue_size,
        debug=args.debug,
    )

    # Set initial voice mode
    if args.no_voice:
        test.toggle_voice_mode()

    # Wait for models to load
    if not test.wait_for_model_loading():
        print("Model loading timed out. Make sure required services are running.")
        return

    # Interactive loop
    print("\nEnter messages for the AI. Commands:")
    print("  'exit' - Quit the program")
    print("  'history' - Show conversation history")
    print("  'voice' - Toggle voice mode on/off")
    print("  'stream [text]' - Stream text directly to TTS")
    print("  'clear' - Clear the TTS queue")
    print("  'pause' - Pause speech playback")
    print("  'resume' - Resume speech playback")
    print("  'flush' - Process all pending text immediately")
    print("  'status' - Print TTS status information")

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue
        elif user_input.lower() == "exit":
            break
        elif user_input.lower() == "history":
            test.show_conversation_history()
        elif user_input.lower() == "voice":
            test.toggle_voice_mode()
        elif user_input.lower() == "clear":
            print("[INFO] Clearing TTS queue")
            test.tts.clear()
        elif user_input.lower() == "pause":
            print("[INFO] Pausing speech")
            test.tts.pause()
        elif user_input.lower() == "resume":
            print("[INFO] Resuming speech")
            test.tts.start()
        elif user_input.lower() == "flush":
            print("[INFO] Flushing text buffer")
            test.tts.flush()
        elif user_input.lower() == "status":
            print("[INFO] Printing TTS status")
            test.print_tts_status()
        elif user_input.lower().startswith("stream "):
            text_to_stream = user_input[7:].strip()
            if text_to_stream:
                print(f"[INFO] Streaming text: {text_to_stream}")
                test.tts.stream_text(text_to_stream)
                # Always flush after streaming specific text to ensure it's played
                test.tts.flush()
        else:
            test.generate_response(user_input)
            # Wait for TTS to complete if voice mode is enabled
            if test.voice_mode:
                test.tts.wait_for_completion(timeout=30.0)


if __name__ == "__main__":
    main()
