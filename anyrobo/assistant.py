"""Core assistant module for AnyRobo."""

import signal
import tkinter as tk
from threading import Event
from typing import Any, Dict, Optional

from anyrobo.bot_handler import BotHandler
from anyrobo.brain.llm_handler import LLMHandler
from anyrobo.speech.stt_handler import STTHandler
from anyrobo.speech.tts_handler import TTSHandler
from anyrobo.ui.ui_handler import UIHandler


class AnyRobo:
    """
    Main assistant class that coordinates speech recognition, synthesis, language model, and UI.

    Uses an event-driven architecture with specialized handlers for each component.
    """

    def __init__(
        self,
        model_name: str = "llama3.2",
        sample_rate: int = 24000,
        silence_threshold: float = 0.02,
        silence_duration: float = 1.5,
        voice: str = "am_michael",
        speed: float = 1.2,
        system_prompt: Optional[str] = None,
        fullscreen: bool = False,
        dangerous_mode: bool = False,
        debug: bool = False,
    ):
        """
        Initialize the AnyRobo assistant.

        Args:
            model_name: Name of the LLM model to use
            sample_rate: Audio sample rate in Hz
            silence_threshold: Volume level that counts as silence
            silence_duration: Seconds of silence before cutting recording
            voice: Voice profile to use
            speed: Speech speed factor
            system_prompt: Custom system prompt for the LLM
            fullscreen: Start UI in fullscreen mode
            dangerous_mode: Use dangerous theme in UI
            debug: Enable debug logging
        """
        # Default system prompt if none provided
        if system_prompt is None:
            system_prompt = (
                "Give a conversational response to the following statement or question in 1-2 sentences. "
                "The response should be natural and engaging, and the length depends on what you have to say."
            )

        # Initialize the main thread event
        self.shutdown_event = Event()
        signal.signal(signal.SIGINT, self._signal_handler)

        # Initialize components in proper order
        self.llm_handler = LLMHandler(model_name=model_name, system_prompt=system_prompt)
        self.stt_handler = STTHandler(
            sample_rate=sample_rate,
            silence_threshold=silence_threshold,
            silence_duration=silence_duration,
        )
        self.tts_handler = TTSHandler(voice=voice, speed=speed)

        # Main coordinator (wires all components together)
        self.bot_handler = BotHandler(
            llm_handler=self.llm_handler,
            stt_handler=self.stt_handler,
            tts_handler=self.tts_handler,
            debug=debug,
        )

        # UI parameters for initialization
        self.root = None
        self.ui_handler = None
        self.ui_params = {
            "theme": "dangerous" if dangerous_mode else "default",
            "fullscreen": fullscreen,
        }

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle interrupt signals."""
        print("\nStopping...")
        self.shutdown_event.set()
        self.stop()

    def _connect_handlers(self) -> None:
        """Connect UI and bot events to create a complete system."""
        # Connect UI actions to bot actions
        self.ui_handler.subscribe_to_event(
            self.ui_handler.ACTION_BUTTON_PRESSED,
            lambda data: self._handle_button_press(data.get("button_id", ""))
            if "button_id" in data
            else None,
        )

        self.ui_handler.subscribe_to_event(
            self.ui_handler.USER_INPUT_RECEIVED,
            lambda data: self.bot_handler.generate_response(data.get("text", ""))
            if "text" in data
            else None,
        )

        # Connect bot status to UI status
        self.bot_handler.subscribe_to_event(
            self.bot_handler.STATUS_CHANGED,
            lambda data: self._handle_status_update(data.get("status", ""))
            if "status" in data
            else None,
        )

        # Connect STT state changes to UI updates
        self.stt_handler.subscribe_to_event(
            self.stt_handler.LISTENING_STARTED,
            lambda _: self.ui_handler.update_record_button_state(True),
        )

        self.stt_handler.subscribe_to_event(
            self.stt_handler.LISTENING_STOPPED,
            lambda _: self.ui_handler.update_record_button_state(False),
        )

        # Connect TTS state changes to UI updates
        self.tts_handler.subscribe_to_event(
            self.tts_handler.SPEECH_STARTED, lambda _: self._handle_status_update("Speaking")
        )

        self.tts_handler.subscribe_to_event(
            self.tts_handler.SPEECH_ENDED, lambda _: self._handle_status_update("Ready for input")
        )

        # Connect bot messages to UI
        self.bot_handler.subscribe_to_event(
            self.bot_handler.USER_MESSAGE,
            lambda data: self.ui_handler.publish_event(
                self.ui_handler.USER_TEXT_UPDATED, {"text": data.get("text", "")}
            )
            if "text" in data
            else None,
        )

        self.bot_handler.subscribe_to_event(
            self.bot_handler.ASSISTANT_MESSAGE, lambda data: self._handle_assistant_message(data)
        )

        self.bot_handler.subscribe_to_event(
            self.bot_handler.ASSISTANT_MESSAGE_CHUNK,
            lambda data: self._handle_assistant_message_chunk(data),
        )

        # Connect STT audio data to UI for visualization
        self.stt_handler.subscribe_to_event(
            "stt.audio.data",  # Custom event for audio visualization data
            lambda data: self._handle_audio_data(data.get("audio_data"))
            if "audio_data" in data
            else None,
        )

        # Connect errors to UI
        self.bot_handler.subscribe_to_event(
            self.bot_handler.ERROR,
            lambda data: self.ui_handler.publish_event(
                self.ui_handler.ERROR_DISPLAYED, {"text": data.get("error", "")}
            )
            if "error" in data
            else None,
        )

    def _handle_button_press(self, button_id: str) -> None:
        """
        Handle button press events from the UI.

        Args:
            button_id: The ID of the button that was pressed
        """
        if button_id == "record":
            self.bot_handler.toggle_listening()
        elif button_id == "clear":
            # Add other button handlers as needed
            pass

    def _handle_status_update(self, status: str) -> None:
        """
        Handle status updates from the bot handler.

        Also updates the UI record button state based on listening status.

        Args:
            status: The new status
        """
        # Update the UI status
        self.ui_handler.publish_event(self.ui_handler.STATUS_UPDATED, {"status": status})

        # Update record button based on listening status
        is_listening = status in ["Listening", "Processing", "Ready for input"]
        self.ui_handler.update_record_button_state(is_listening)

    def _handle_audio_data(self, audio_data: Any) -> None:
        """
        Handle audio data from the STT handler and update the UI visualization.

        Args:
            audio_data: Audio data as numpy array
        """
        if (
            audio_data is not None
            and hasattr(self.ui_handler, "audio_vis")
            and self.ui_handler.audio_vis is not None
        ):
            # Scale the audio data to make visualization more visible
            scaled_audio = audio_data * 5.0
            self.ui_handler.audio_vis.set_audio_data(scaled_audio)

    def _handle_assistant_message(self, data: Dict[str, Any]) -> None:
        """
        Handle full assistant message by updating the UI.

        Args:
            data: Message data including text and response ID
        """
        if "text" in data:
            self.ui_handler.publish_event(
                self.ui_handler.ASSISTANT_TEXT_UPDATED,
                {"text": data.get("text", ""), "response_id": data.get("response_id", "")},
            )

    def _handle_assistant_message_chunk(self, data: Dict[str, Any]) -> None:
        """
        Handle assistant message chunk by updating the UI progressively.

        Args:
            data: Message chunk data including text and response ID
        """
        if "text" in data:
            self.ui_handler.publish_event(
                self.ui_handler.ASSISTANT_TEXT_UPDATED,
                {"text": data.get("text", ""), "response_id": data.get("response_id", "")},
            )

    def start(self) -> None:
        """Start the assistant and UI."""
        # Create Tkinter root window
        self.root = tk.Tk()

        # Initialize UI handler with root window
        self.ui_handler = UIHandler(
            root=self.root, theme=self.ui_params["theme"], fullscreen=self.ui_params["fullscreen"]
        )

        # Connect all component handlers
        self._connect_handlers()

        # Start bot in listening mode
        self.bot_handler.start_listening()

        # Update initial UI status
        self.ui_handler.publish_event(self.ui_handler.STATUS_UPDATED, {"status": "Ready"})

        print("AnyRobo assistant started. Press Ctrl+C to stop.")

        # Start main UI loop (will block until window is closed)
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"UI error: {e}")
        finally:
            # If we get here, the UI has been closed
            if not self.shutdown_event.is_set():
                self.stop()

    def stop(self) -> None:
        """Stop the assistant and clean up resources."""
        # Clean up bot handler (will handle its own cleanup of handlers)
        if hasattr(self, "bot_handler") and self.bot_handler:
            self.bot_handler.cleanup()

        # Stop UI if it was initialized
        if self.root and self.root.winfo_exists():
            try:
                self.root.destroy()
            except:
                pass

        print("AnyRobo assistant stopped.")


def create_assistant(**kwargs) -> AnyRobo:
    """
    Create and return an AnyRobo assistant instance.

    Args:
        **kwargs: Arguments to pass to AnyRobo constructor

    Returns:
        An initialized AnyRobo assistant
    """
    return AnyRobo(**kwargs)
