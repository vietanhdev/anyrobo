#!/usr/bin/env python3
"""
Text-to-Speech Test Example

This example demonstrates how to use the TTSHandler to perform text-to-speech
synthesis using the AnyRobo framework.
"""

import argparse
import time
from typing import Any, Dict

from anyrobo.speech.tts_handler import TTSHandler
from anyrobo.utils.events import EventBus


class TextToSpeechTest:
    """
    Test class for text-to-speech synthesis using the TTSHandler.

    This class demonstrates how to use the TTSHandler to convert text
    to speech and play it in real-time.
    """

    def __init__(
        self,
        voice: str = "af_heart",
        speed: float = 1.5,
        sample_rate: int = 16000,
        chunk_size: int = 500,
        max_queue_size: int = 20,
        debug: bool = False,
    ) -> None:
        """
        Initialize the text-to-speech test.

        Args:
            voice: Voice ID to use
            speed: Speech speed multiplier
            sample_rate: Audio sample rate
            chunk_size: Maximum size of text chunks (in characters)
            max_queue_size: Maximum number of audio chunks to queue
            debug: Enable debug output
        """
        # Create the central event bus
        self.event_bus = EventBus()

        # Create TTS handler
        self.tts = TTSHandler(
            voice=voice,
            speed=speed,
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            max_queue_size=max_queue_size,
            debug=debug,
        )

        # Override the default event bus in TTSHandler
        self.tts._event_bus = self.event_bus

        # Register event handlers
        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        """Register event handlers for TTS events."""
        self.event_bus.subscribe(TTSHandler.SPEECH_STARTED, self._on_speech_started)
        self.event_bus.subscribe(TTSHandler.SPEECH_ENDED, self._on_speech_ended)
        self.event_bus.subscribe(TTSHandler.SPEECH_CHUNK_STARTED, self._on_speech_chunk_started)
        self.event_bus.subscribe(TTSHandler.SPEECH_CHUNK_ENDED, self._on_speech_chunk_ended)
        self.event_bus.subscribe(TTSHandler.SPEECH_ERROR, self._on_speech_error)
        self.event_bus.subscribe(TTSHandler.MODEL_LOADED, self._on_model_loaded)
        self.event_bus.subscribe(TTSHandler.SPEECH_PAUSED, self._on_speech_paused)
        self.event_bus.subscribe(TTSHandler.SPEECH_RESUMED, self._on_speech_resumed)

    def _on_speech_started(self, data: Any) -> None:
        """Handle speech started event."""
        print("\n[INFO] Speech playback started")

    def _on_speech_ended(self, data: Any) -> None:
        """Handle speech ended event."""
        canceled = data.get("canceled", False) if data else False
        if canceled:
            print("\n[INFO] Speech playback canceled")
        else:
            print("\n[INFO] Speech playback ended")

    def _on_speech_chunk_started(self, data: Dict[str, Any]) -> None:
        """Handle speech chunk started event."""
        chunk_num = data.get("chunk_num", 0) if data else 0
        print(f"\n[INFO] Playing chunk {chunk_num}")

    def _on_speech_chunk_ended(self, data: Dict[str, Any]) -> None:
        """Handle speech chunk ended event."""
        chunk_num = data.get("chunk_num", 0) if data else 0
        print(f"[INFO] Finished chunk {chunk_num}")

    def _on_speech_error(self, data: Dict[str, Any]) -> None:
        """Handle speech error event."""
        error = data.get("error", "Unknown error") if data else "Unknown error"
        print(f"\n[ERROR] Speech error: {error}")

    def _on_speech_paused(self, data: Any) -> None:
        """Handle speech paused event."""
        print("\n[INFO] Speech playback paused")

    def _on_speech_resumed(self, data: Any) -> None:
        """Handle speech resumed event."""
        print("\n[INFO] Speech playback resumed")

    def _on_model_loaded(self, data: Dict[str, Any]) -> None:
        """Handle model loaded event."""
        voice = data.get("voice", "unknown") if data else "unknown"
        print(f"[INFO] TTS model loaded successfully with voice {voice}")

    def speak_text(self, text: str) -> None:
        """
        Speak the given text using the TTS handler.

        Args:
            text: Text to synthesize and play
        """
        print(f'\n[INFO] Speaking: "{text}"')
        self.tts.stream_text(text)
        self.tts.flush()  # Force immediate processing

        # Wait for speech to complete
        self.tts.wait_for_completion(timeout=30.0)

    def speak_streaming(self, text: str) -> None:
        """
        Speak the given text in streaming mode.

        Args:
            text: Text to synthesize and play
        """
        # Split text into smaller chunks to simulate streaming
        chunks = text.split(". ")
        chunks = [chunk + "." for chunk in chunks[:-1]] + [chunks[-1]]

        print(f'\n[INFO] Speaking in streaming mode: "{text}"')

        for i, chunk in enumerate(chunks):
            print(f'[INFO] Streaming chunk {i+1}/{len(chunks)}: "{chunk}"')
            self.tts.stream_text(chunk)
            # Small pause between chunks
            time.sleep(0.2)

        # Flush any remaining text in buffer
        self.tts.flush()

        # Wait for speech to complete
        self.tts.wait_for_completion(timeout=30.0)

    def print_status(self) -> None:
        """Print the current TTS status."""
        self.tts.print_status()

    def run_demo(self) -> None:
        """Run the text-to-speech demo with various examples."""
        try:
            print("Starting Text-to-Speech Demo")
            print("=" * 50)
            print("Voice: ", self.tts.voice)
            print("Speed: ", self.tts.speed)
            print("Sample Rate: ", self.tts.sample_rate)
            print("Chunk Size: ", self.tts.chunk_size)
            print("=" * 50)
            print("Press Ctrl+C to stop the demo at any time")

            # Wait for model to load
            print("\n[INFO] Waiting for TTS model to load...")
            time.sleep(2)

            # Example 1: Simple sentence
            self.speak_text("Hello, this is a test of the AnyRobo text to speech system.")
            time.sleep(1)

            # Example 2: Longer paragraph
            self.speak_text(
                "Text to speech conversion allows computer systems to convert written text "
                "into spoken audio. This technology has many applications, including "
                "accessibility for people with visual impairments, virtual assistants, "
                "and automated customer service systems."
            )
            time.sleep(1)

            # Example 3: Speaking in streaming mode
            self.speak_streaming(
                "This is an example of streaming text to speech. The text is sent in "
                "smaller chunks to simulate a real-time response. This approach is "
                "commonly used in conversational AI systems and voice assistants. "
                "It allows for lower latency responses in interactive applications."
            )
            
            # Example 4: Demonstrating pause and resume
            print("\n[INFO] Demonstrating pause and resume...")
            self.tts.stream_text("This sentence will be paused in the middle and then resumed. ")
            self.tts.flush()
            time.sleep(2)  # Wait for part of it to play
            
            # Pause playback
            self.tts.pause()
            print("[INFO] Paused playback for 2 seconds...")
            time.sleep(2)
            
            # Resume playback
            self.tts.start()
            self.tts.stream_text("Now the speech is continuing after being paused.")
            self.tts.flush()
            self.tts.wait_for_completion(timeout=30.0)

            print("\n[INFO] Demo completed successfully")

        except KeyboardInterrupt:
            print("\n\nDemo interrupted by user")
        finally:
            # Cleanup
            self.tts.cleanup()
            print("\nText-to-Speech Demo completed.")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test text-to-speech using AnyRobo")
    parser.add_argument(
        "--voice", type=str, default="af_heart", help="Voice ID to use (default: af_heart)"
    )
    parser.add_argument(
        "--speed", type=float, default=1.5, help="Speech speed multiplier (default: 1.5)"
    )
    parser.add_argument(
        "--sample-rate", type=int, default=16000, help="Audio sample rate (default: 16000)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Maximum size of text chunks in characters (default: 500)",
    )
    parser.add_argument(
        "--max-queue-size", type=int, default=20, help="Maximum audio queue size (default: 20)"
    )
    parser.add_argument("--text", type=str, help="Specific text to speak (bypasses the demo)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    return parser.parse_args()


def interactive_mode(test: TextToSpeechTest) -> None:
    """Run the TTS in interactive mode with commands."""
    print("\nInteractive TTS mode. Available commands:")
    print("  'exit' - Quit the program")
    print("  'speak [text]' - Speak the provided text")
    print("  'stream [text]' - Stream text to TTS")
    print("  'clear' - Clear the TTS queue")
    print("  'pause' - Pause speech playback")
    print("  'resume' - Resume speech playback")
    print("  'flush' - Process all pending text immediately")
    print("  'status' - Print TTS status information")

    while True:
        user_input = input("\nCommand: ").strip()

        if not user_input:
            continue
        elif user_input.lower() == "exit":
            break
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
            test.print_status()
        elif user_input.lower().startswith("speak "):
            text = user_input[6:].strip()
            if text:
                test.speak_text(text)
        elif user_input.lower().startswith("stream "):
            text = user_input[7:].strip()
            if text:
                print(f"[INFO] Streaming text: {text}")
                test.tts.stream_text(text)
        else:
            print("Unknown command. Type 'exit' to quit.")


if __name__ == "__main__":
    args = parse_args()

    test = TextToSpeechTest(
        voice=args.voice,
        speed=args.speed,
        sample_rate=args.sample_rate,
        chunk_size=args.chunk_size,
        max_queue_size=args.max_queue_size,
        debug=args.debug,
    )

    if args.interactive:
        interactive_mode(test)
    elif args.text:
        # If text is provided, just speak that
        test.speak_text(args.text)
    else:
        # Otherwise run the demo
        test.run_demo()
