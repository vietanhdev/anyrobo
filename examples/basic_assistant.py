#!/usr/bin/env python3
"""Example of creating a JARVIS-like assistant with AnyRobo."""

import time
from anyrobo import AnyRobo
from anyrobo.models.loader import download_tts_model, ensure_ollama_model


def main():
    """Run a JARVIS-like AI assistant."""
    # Make sure required models are available
    download_tts_model()  # TTS model
    ensure_ollama_model("llama3.2")  # LLM
    
    # Configure the assistant with JARVIS personality
    assistant = AnyRobo(
        # Audio settings
        sample_rate=24000,
        silence_threshold=0.02,
        silence_duration=1.5,
        
        # Speech settings
        voice="am_michael",  # Using a masculine voice for JARVIS
        speed=1.2,
        
        # JARVIS personality
        system_prompt=(
            "You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), "
            "the advanced AI assistant created by Tony Stark. "
            "You have a British accent, dry wit, and immense technical knowledge. "
            "You are polite, efficient, and occasionally sarcastic. "
            "Your responses should be concise, intelligent, and slightly playful. "
            "You often address the user as 'sir' or 'madam' and have a subtle sense of humor."
        )
    )
    
    print("Initializing J.A.R.V.I.S. interface...")
    print("All systems online. Voice recognition activated.")
    print("Awaiting your command, sir.")
    print("Press Ctrl+C to exit.")
    print("")
    
    try:
        # This starts the main loop of listening and responding
        assistant.record_and_transcribe()
    except KeyboardInterrupt:
        print("\nJ.A.R.V.I.S. shutting down...")


if __name__ == "__main__":
    main() 