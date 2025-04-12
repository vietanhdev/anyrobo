"""Command-line interface for AnyRobo."""

import argparse
import sys
from typing import List, Optional

from anyrobo import AnyRobo
from anyrobo.models.loader import download_tts_model, download_whisper_model, ensure_ollama_model


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Command-line arguments

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="AnyRobo - Voice-powered AI assistant")

    parser.add_argument(
        "--voice", type=str, default="af_sarah", help="Voice profile to use (default: af_sarah)"
    )

    parser.add_argument(
        "--speed", type=float, default=1.2, help="Speed factor for speech (default: 1.2)"
    )

    parser.add_argument(
        "--silence-threshold",
        type=float,
        default=0.02,
        help="Volume level that counts as silence (default: 0.02)",
    )

    parser.add_argument(
        "--silence-duration",
        type=float,
        default=1.5,
        help="Seconds of silence before cutting recording (default: 1.5)",
    )

    parser.add_argument(
        "--sample-rate", type=int, default=24000, help="Audio sample rate in Hz (default: 24000)"
    )

    parser.add_argument(
        "--model", type=str, default="llama3.2", help="Ollama model to use (default: llama3.2)"
    )

    parser.add_argument("--prompt", type=str, default=None, help="Custom system prompt for the LLM")

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Download required models without starting the assistant",
    )

    return parser.parse_args(args)


def setup_models() -> None:
    """Download required models."""
    print("Setting up AnyRobo...")
    tts_model_path = download_tts_model()
    whisper_model_dir = download_whisper_model("small")
    ensure_ollama_model("llama3.2")
    print("\nSetup complete! You can now run AnyRobo.")


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for AnyRobo.

    Args:
        args: Command-line arguments

    Returns:
        Exit code
    """
    parsed_args = parse_args(args)

    # Just setup models if requested
    if parsed_args.setup:
        setup_models()
        return 0

    # Create and run the assistant
    try:
        # Make sure models are available
        tts_model_path = download_tts_model()
        whisper_model_dir = download_whisper_model("small")
        ensure_ollama_model(parsed_args.model)

        # Create the assistant
        assistant = AnyRobo(
            sample_rate=parsed_args.sample_rate,
            silence_threshold=parsed_args.silence_threshold,
            silence_duration=parsed_args.silence_duration,
            voice=parsed_args.voice,
            speed=parsed_args.speed,
            system_prompt=parsed_args.prompt,
        )

        print("Starting AnyRobo - your voice-powered AI assistant...")
        print(f"Using voice: {parsed_args.voice}")
        print(f"Using model: {parsed_args.model}")
        print("Press Ctrl+C to stop")

        # Run the assistant
        assistant.record_and_transcribe()
        return 0
    except KeyboardInterrupt:
        print("\nStopping AnyRobo...")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
