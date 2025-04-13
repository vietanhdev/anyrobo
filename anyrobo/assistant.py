"""Core assistant module for AnyRobo."""

import signal
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from typing import Any, Dict, List, Optional

import numpy as np
import sounddevice as sd
from ollama import chat

from anyrobo.speech.recognition import SpeechRecognizer
from anyrobo.speech.synthesis import TextToSpeech


class AnyRobo:
    """Main assistant class that coordinates speech recognition and synthesis."""

    def __init__(
        self,
        sample_rate: int = 24000,
        silence_threshold: float = 0.02,
        silence_duration: float = 1.5,
        voice: str = "am_michael",
        speed: float = 1.2,
        system_prompt: Optional[str] = None,
    ):
        """Initialize the AnyRobo assistant.

        Args:
            sample_rate: Audio sample rate in Hz
            silence_threshold: Volume level that counts as silence
            silence_duration: Seconds of silence before cutting recording
            voice: Voice profile to use
            speed: Speech speed factor
            system_prompt: Custom system prompt for the LLM
        """
        # audio settings
        self.SAMPLE_RATE = sample_rate
        self.SILENCE_THRESHOLD = silence_threshold
        self.SILENCE_DURATION = silence_duration

        # text-to-speech settings
        self.SPEED = speed
        self.VOICE = voice
        self.CHUNK_SIZE = 300  # size of text chunks for processing

        # ollama settings
        self.messages: List[Dict[str, str]] = []
        self.SYSTEM_PROMPT = (
            system_prompt
            or "Give a conversational response to the following statement or question in 1-2 sentences. The response should be natural and engaging, and the length depends on what you have to say."
        )

        # init components
        self.speech_recognizer = SpeechRecognizer(model="small", batch_size=12)
        self.tts = TextToSpeech()
        self.executor = ThreadPoolExecutor(max_workers=1)

        # interrupt handling
        self.shutdown_event = Event()
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle interrupt signals."""
        print("\nStopping...")
        self.shutdown_event.set()

    def record_and_transcribe(self) -> None:
        """Main loop: record audio, transcribe, and respond."""
        # state for audio recording
        audio_buffer = []
        silence_frames = 0
        total_frames = 0

        def callback(
            indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
        ) -> None:
            # callback function that processes incoming audio frames
            if self.shutdown_event.is_set():
                raise sd.CallbackStop()

            nonlocal audio_buffer, silence_frames, total_frames

            if status:
                print(status)

            audio = indata.flatten()
            level = np.abs(audio).mean()

            audio_buffer.extend(audio.tolist())
            total_frames += len(audio)

            # track silence duration
            if level < self.SILENCE_THRESHOLD:
                silence_frames += len(audio)
            else:
                silence_frames = 0

            # process audio when silence is detected
            if silence_frames > self.SILENCE_DURATION * self.SAMPLE_RATE:
                audio_segment = np.array(audio_buffer, dtype=np.float32)

                if len(audio_segment) > self.SAMPLE_RATE:
                    text = self.speech_recognizer.transcribe(audio_segment)["text"]

                    # skip empty/invalid transcriptions
                    if text.strip():
                        print(f"Transcription: {text}")
                        self.messages.append({"role": "user", "content": text})
                        self.create_and_play_response(text)

                # reset state
                audio_buffer.clear()
                silence_frames = 0
                total_frames = 0

        # start recording loop
        try:
            with sd.InputStream(
                callback=callback, channels=1, samplerate=self.SAMPLE_RATE, dtype=np.float32
            ):
                print("Recording... Press Ctrl+C to stop")
                while not self.shutdown_event.is_set():
                    sd.sleep(100)
        except sd.CallbackStop:
            pass

    def create_and_play_response(self, prompt: str) -> None:
        """Generate and speak a response to the user's input."""
        if self.shutdown_event.is_set():
            return

        # stream response from llm
        stream = chat(
            model="llama3.2",
            messages=[{"role": "system", "content": self.SYSTEM_PROMPT}] + self.messages,
            stream=True,
        )

        # state for processing response
        futures = []
        buffer = ""
        curr_str = ""

        try:
            # process response stream
            for chunk in stream:
                if self.shutdown_event.is_set():
                    break

                print(chunk)
                text = chunk["message"]["content"]

                if len(text) == 0:
                    self.messages.append({"role": "assistant", "content": curr_str})
                    curr_str = ""
                    print(self.messages)
                    continue

                buffer += text
                curr_str += text

                # find end of sentence to chunk at
                last_punctuation = max(buffer.rfind(". "), buffer.rfind("? "), buffer.rfind("! "))

                if last_punctuation == -1:
                    continue

                # handle long chunks
                while last_punctuation != -1 and last_punctuation >= self.CHUNK_SIZE:
                    last_punctuation = max(
                        buffer.rfind(", ", 0, last_punctuation),
                        buffer.rfind("; ", 0, last_punctuation),
                        buffer.rfind("— ", 0, last_punctuation),
                    )

                if last_punctuation == -1:
                    last_punctuation = buffer.find(" ", 0, self.CHUNK_SIZE)

                # process chunk
                # convert chunk to audio
                chunk_text = buffer[: last_punctuation + 1]
                futures.append(
                    self.executor.submit(
                        self.tts.generate_audio, chunk_text, self.VOICE, self.SPEED
                    )
                )
                buffer = buffer[last_punctuation + 1 :]

            # process final chunk if any
            if buffer and not self.shutdown_event.is_set():
                futures.append(
                    self.executor.submit(self.tts.generate_audio, buffer, self.VOICE, self.SPEED)
                )

            # play generated audio
            if not self.shutdown_event.is_set():
                with sd.OutputStream(
                    samplerate=self.SAMPLE_RATE, channels=1, dtype=np.float32
                ) as out_stream:
                    for fut in futures:
                        if self.shutdown_event.is_set():
                            break
                        audio_data = fut.result()
                        if len(audio_data) == 0:
                            continue
                        out_stream.write(audio_data.reshape(-1, 1))
        except Exception as e:
            if not self.shutdown_event.is_set():
                raise e
