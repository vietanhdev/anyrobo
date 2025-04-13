# AnyRobo - Create Your Own Robo Assistant

AnyRobo is an advanced speech-to-speech AI assistant framework that enables you to create your own real-life version of sci-fi AI assistants like JARVIS (from Iron Man) or GLADOS (from Portal). Powered by state-of-the-art machine learning models, AnyRobo listens to your voice, understands your requests, and responds with natural-sounding speech in real-time.

![AnyRobo](https://img.shields.io/badge/AnyRobo-0.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Why AnyRobo?

Have you ever wanted to create your own JARVIS or GLADOS? AnyRobo provides a fully modular framework that allows you to:

- Create voice-powered AI assistants with unique personalities
- Customize voice profiles to sound like your favorite AI characters
- Build advanced conversation capabilities with state-of-the-art language models
- Deploy your assistant on macOS with optimized performance for Apple Silicon

## Core Technologies

- **Speech Recognition**: [Whisper MLX](https://github.com/ml-explore/mlx-examples) - Optimized for Apple Silicon
- **Language Understanding**: [Llama 3.2](https://ollama.com/library/llama3.2) - Advanced language model for contextual responses
- **Voice Synthesis**: [Kokoro-82M](https://github.com/thewh1teagle/kokoro-onnx) - High-quality text-to-speech

## Features

- **Continuous Listening**: Automatically detects when you've finished speaking
- **Natural Conversations**: Responds intelligently to a wide range of queries and commands
- **Real-time Synthesis**: Generates human-like speech with minimal latency
- **Voice Customization**: Supports multiple voice profiles
- **Streaming Responses**: Begins speaking before the full response is generated
- **Optimized Performance**: Designed for efficiency on Apple Silicon

## Plan

- [ ] JARVIS assistant with UI
- [ ] Natural voice interaction
- [ ] Functional calling
- [ ] Web search
- [ ] MCP support
- [ ] Computer vision: See what's in front of the camera
- [ ] Build your own AI character
- [ ] 3D-printed JARVIS case
- [ ] GLADOS assistant with UI
- [ ] 3D-printed GLADOS case
- [ ] Physical button to trigger actions
- [ ] Physical robot bodies
- [ ] .... [add your ideas here]

## Installation

### Quick Install (from PyPI)

```bash
pip install anyrobo
```

### Install from Source

```bash
git clone https://github.com/vietanhdev/anyrobo.git
cd anyrobo
pip install -e .
```

### Setup Dependencies

AnyRobo requires [Ollama](https://ollama.com/) for LLM support:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
# Pull the required model
ollama pull llama3.2
```

## Usage

- Test voice assistant:

```bash
python examples/test_assistant.py
```

## Create Your Own AI Character

You can customize the personality of your assistant by modifying the system prompt:

```python
# JARVIS from Iron Man
system_prompt = (
    "You are J.A.R.V.I.S., an advanced AI assistant. "
    "Respond with a mix of helpfulness, light sarcasm, and technical prowess."
)

# GLADOS from Portal
system_prompt = (
    "You are GLaDOS, an AI with a dark sense of humor. "
    "Respond to queries sarcastically, occasionally mentioning cake or testing."
)

# HAL 9000 from 2001: A Space Odyssey
system_prompt = (
    "You are HAL 9000. Be calm, logical, and slightly ominous in your responses. "
    "Speak in a slow, deliberate manner and be excessively literal."
)
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `voice` | Voice profile to use | `"am_michael"` |
| `speed` | Speed factor for speech | `1.2` |
| `silence_threshold` | Volume level that counts as silence | `0.02` |
| `silence_duration` | Seconds of silence before cutting recording | `1.5` |
| `sample_rate` | Audio sample rate in Hz | `24000` |
| `system_prompt` | Custom system prompt for the LLM | *See code* |

## Troubleshooting

- **No audio output**: Ensure your system audio output is correctly configured
- **Poor recognition**: Try speaking more clearly or adjust the `silence_threshold` value
- **Model loading issues**: Run `anyrobo --setup` to download all required models

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

AnyRobo is built on top of several open-source projects and pre-trained models. We're grateful to the developers and researchers who make their work available to the community.
