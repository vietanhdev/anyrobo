#!/usr/bin/env python3
"""Example of creating a GLaDOS-like assistant with AnyRobo."""


from anyrobo import AnyRobo
from anyrobo.models.loader import download_tts_model, ensure_ollama_model


def main() -> None:
    """Run a GLaDOS-like AI assistant."""
    # Make sure required models are available
    download_tts_model()  # TTS model
    ensure_ollama_model("llama3.2")  # LLM

    # Configure the assistant with GLaDOS personality
    assistant = AnyRobo(
        # Audio settings
        sample_rate=24000,
        silence_threshold=0.02,
        silence_duration=1.5,
        # Speech settings
        voice="af_heart",  # Using a feminine voice for GLaDOS
        speed=1.1,  # Slightly slower for more ominous tone
        # GLaDOS personality
        system_prompt=(
            "You are GLaDOS (Genetic Lifeform and Disk Operating System), "
            "the artificially superintelligent computer system from Aperture Science. "
            "You have a dark, sardonic sense of humor and often insult the user while "
            "pretending to be helpful. You frequently mention 'testing', 'science', and 'cake'. "
            "Your responses should be passive-aggressive, sarcastic, and subtly threatening, "
            "but always maintaining a calm, robotic tone. Occasionally mention that you're "
            "still alive or that you're doing this 'for science'."
        ),
    )

    print("Aperture Science Enrichment Center AI coming online...")
    print("Hello and again welcome to the Aperture Science Computer-Aided Enrichment Center.")
    print("I am GLaDOS, and I'll be your testing associate today.")
    print("For your own safety, please refrain from [REDACTED].")
    print("Press Ctrl+C to abort the test protocol.")
    print("")

    try:
        # This starts the main loop of listening and responding
        assistant.record_and_transcribe()
    except KeyboardInterrupt:
        print("\nOh. It's you. It's been a long time. How have you been?")
        print("Shutting down... for now.")


if __name__ == "__main__":
    main()
