"""Model loader utilities for AnyRobo."""

import os
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_models_dir() -> Path:
    """Get the directory where models should be stored.

    Returns:
        Path to the models directory
    """
    # Use ~/.anyrobo as the default models directory
    home_dir = Path.home()
    models_dir = home_dir / ".anyrobo"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def download_tts_model(model_path: Optional[str] = None) -> str:
    """Download the Kokoro TTS model if not already present.

    Args:
        model_path: Optional custom path to save the model

    Returns:
        Path to the downloaded model
    """
    if model_path is None:
        models_dir = get_models_dir()
        # Use the smaller INT8 model
        model_path = os.path.join(models_dir, "kokoro-v0_19.int8.onnx")

    voices_path = os.path.join(os.path.dirname(model_path), "voices-v1.0.bin")

    # Check if the model already exists
    if os.path.exists(model_path):
        print(f"TTS model already exists at {model_path}")
    else:
        # Download the model
        print(f"Downloading TTS model to {model_path}")
        url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.int8.onnx"
        urllib.request.urlretrieve(url, model_path)
        print("Model download complete")

    # Check if voices file exists
    if os.path.exists(voices_path):
        print(f"TTS voices file already exists at {voices_path}")
    else:
        # Download the voices file
        print(f"Downloading TTS voices file to {voices_path}")
        url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
        urllib.request.urlretrieve(url, voices_path)
        print("Voices download complete")

    return model_path


def download_whisper_model(model_size: str = "small") -> str:
    """Download or prepare the Whisper MLX model.

    Args:
        model_size: Model size (small, medium, large)

    Returns:
        Path to the model directory
    """
    models_dir = get_models_dir() / "whisper" / model_size
    models_dir.mkdir(parents=True, exist_ok=True)

    # The LightningWhisperMLX library handles downloading automatically,
    # but we can set up the directory structure
    print(f"Whisper {model_size} model will be used from {models_dir}")

    return str(models_dir)


def ensure_ollama_model(model_name: str = "llama3.2") -> None:
    """Ensure the Ollama model is installed.

    Args:
        model_name: Name of the Ollama model
    """
    print(f"Checking for Ollama model {model_name}")

    try:
        # Use the Python Ollama client instead of subprocess
        from ollama import list, pull

        # Get list of installed models
        models_response = list()
        models_list: List[Dict[str, Any]] = models_response.get("models", [])

        # Check if model exists
        if any(model.get("name") == model_name for model in models_list):
            print(f"Ollama model {model_name} is already installed")
            return

        # If not found, pull the model
        print(f"Pulling Ollama model {model_name}")
        pull(model_name)
        print(f"Ollama model {model_name} installed successfully")
    except ImportError:
        print("Warning: Ollama Python client not found.")
        print("Please install it with 'pip install ollama'")
    except Exception as e:
        print(f"Warning: Failed to check/install Ollama model: {e}")
        print("Please make sure Ollama is installed and running")
