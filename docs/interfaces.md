# AnyRobo Component Interfaces

This document outlines the interfaces for various components in the AnyRobo framework, including their configurations, events, and usage patterns.

## Speech-to-Text Handler (STTHandler)

The `STTHandler` class in `anyrobo.speech.stt_handler` provides speech recognition capabilities for the AnyRobo framework.

### Description

`STTHandler` manages audio input and speech recognition. It listens to audio from the microphone, detects speech activity, and transcribes the speech using a configurable speech recognition model. It's designed with an event-driven architecture to integrate seamlessly with other components.

### Configuration

The `STTHandler` class accepts the following configuration parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"small"` | Speech recognition model size (options: small, medium, large) |
| `sample_rate` | `int` | `16000` | Audio sample rate in Hz |
| `silence_threshold` | `float` | `0.01` | Threshold for silence detection (0.0-1.0) |
| `silence_duration` | `float` | `1.0` | Duration of silence (in seconds) to consider end of speech |

### Events

The `STTHandler` emits the following events:

| Event Topic | Description | Data Payload |
|-------------|-------------|--------------|
| `stt.listening.started` | Emitted when listening for audio input starts | `None` |
| `stt.listening.stopped` | Emitted when listening for audio input stops | `None` |
| `stt.listening.paused` | Emitted when audio input is temporarily paused | `None` |
| `stt.listening.resumed` | Emitted when audio input resumes from paused state | `None` |
| `stt.transcription.started` | Emitted when speech processing begins | `None` |
| `stt.transcription.result` | Emitted when transcription is complete | `{"text": str, "segments": list, ...}` |
| `stt.transcription.error` | Emitted when an error occurs during transcription | `{"error": str}` |
| `stt.audio.data` | Emitted continuously with audio data for visualization | `{"audio_data": numpy.ndarray}` |

### Methods

| Method | Description | Return Value |
|--------|-------------|--------------|
| `start_listening()` | Start listening for voice input | `bool`: Success status |
| `pause_listening()` | Temporarily pause audio input | `bool`: Success status |
| `resume_listening()` | Resume audio input if paused | `bool`: Success status |
| `stop_listening()` | Stop listening for voice input | `bool`: Success status |
| `is_active()` | Check if STT is actively listening | `bool`: Active status |
| `cleanup()` | Clean up resources | `None` |

### Example Usage

```python
from anyrobo.speech.stt_handler import STTHandler
from anyrobo.utils.events import EventBus

# Create an event bus
event_bus = EventBus()

# Create STT handler
stt = STTHandler(
    model="small",
    sample_rate=16000,
    silence_threshold=0.01,
    silence_duration=1.0
)

# Override the default event bus
stt._event_bus = event_bus

# Subscribe to events
event_bus.subscribe("stt.transcription.result", lambda data: print(f"Transcription: {data['text']}"))

# Start listening
stt.start_listening()

# ... your application logic ...

# Stop listening when done
stt.stop_listening()
stt.cleanup()
```

## Speech Recognizer

The `SpeechRecognizer` class in `anyrobo.speech.recognition` is used by the STTHandler to perform the actual speech recognition.

### Description

This class provides a simplified wrapper around the Lightning Whisper MLX model for speech recognition. It handles the transcription of audio data to text.

### Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"small"` | Whisper model size (small, medium, large) |
| `batch_size` | `int` | `12` | Batch size for processing |

### Methods

| Method | Description | Return Value |
|--------|-------------|--------------|
| `transcribe(audio_data)` | Transcribe speech from audio data | `Dict[str, Any]`: Transcription result |

### Example Usage

```python
import numpy as np
from anyrobo.speech.recognition import SpeechRecognizer

# Create speech recognizer
recognizer = SpeechRecognizer(model="small", batch_size=12)

# Transcribe audio (assuming audio_data is a numpy array of audio samples)
audio_data = np.array([...])  # Audio data at 16kHz sample rate
result = recognizer.transcribe(audio_data)

# Access the transcription text
text = result["text"]
print(f"Transcription: {text}")
```
