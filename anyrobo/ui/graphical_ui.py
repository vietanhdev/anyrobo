"""
Graphical UI implementation for the AnyRobo framework.

Provides integration between the UIHandler component and the graphical UI.
"""

import queue
import threading
import tkinter as tk
from typing import Any, Callable, Dict, Optional

import numpy as np

from anyrobo.ui.animations import CircularProgressAnimation, HexagonGrid, PulsatingCircle, ScanLine
from anyrobo.ui.components import FuturisticButton, StatusBar, TextDisplay
from anyrobo.ui.themes import get_theme
from anyrobo.ui.visualizers import LiveAudioVisualizer


class GraphicalUIHandler:
    """
    Connects UIHandler events with a graphical UI implementation.

    This class serves as a bridge between the abstract UIHandler component
    and concrete graphical UI implementations.
    """

    def __init__(
        self,
        handler: UIHandler,
        fullscreen: bool = False,
        dangerous: bool = False,
        voice_id: str = "af_heart",
        speech_speed: float = 1.0,
    ) -> None:
        """
        Initialize the graphical UI handler.

        Args:
            handler: The UIHandler component to connect with
            fullscreen: Whether to start the UI in fullscreen mode
            dangerous: Whether to use the "dangerous" theme
            voice_id: Voice ID to use for text-to-speech
            speech_speed: Speech speed multiplier (1.0 = normal)
        """
        self._handler = handler
        self.fullscreen = fullscreen
        self.dangerous = dangerous
        self.root: Optional[tk.Tk] = None
        self.running = False
        self.main_thread_queue: queue.Queue = queue.Queue()
        self.audio_data: Optional[np.ndarray] = None

        # UI Components
        self.text_display: Optional[TextDisplay] = None
        self.audio_vis: Optional[LiveAudioVisualizer] = None
        self.hex_grid: Optional[HexagonGrid] = None
        self.scan_line: Optional[ScanLine] = None
        self.circle_progress: Optional[CircularProgressAnimation] = None
        self.pulse_circle: Optional[PulsatingCircle] = None
        self.record_button: Optional[FuturisticButton] = None
        self.status_bar: Optional[StatusBar] = None

        # Set voice and animation settings
        self._handler.set_voice(voice_id)
        self._handler.set_speech_speed(speech_speed)

        # Connect UI Handler callbacks
        self._handler.set_status_callback(self._handle_status_update)
        self._handler.set_user_text_callback(self._handle_user_text)
        self._handler.set_assistant_text_callback(self._handle_assistant_text)
        self._handler.set_voice_command_callback(self._handle_voice_command)
        self._handler.set_theme_changed_callback(self._handle_theme_change)
        self._handler.set_warning_callback(self._handle_warning)
        self._handler.set_error_callback(self._handle_error)
        self._handler.set_system_message_callback(self._handle_system_message)

        # Subscribe to UI events
        self._setup_event_subscriptions()

    def _setup_event_subscriptions(self) -> None:
        """Set up event subscriptions from UIHandler."""
        # Base UI events
        self._handler.subscribe_to_event(self._handler.STATUS_UPDATED, self._handle_status_event)

        self._handler.subscribe_to_event(
            self._handler.USER_TEXT_UPDATED, self._handle_user_text_event
        )

        self._handler.subscribe_to_event(
            self._handler.ASSISTANT_TEXT_UPDATED, self._handle_assistant_text_event
        )

        # Voice events
        self._handler.subscribe_to_event(
            self._handler.VOICE_RECORDING_STARTED, self._handle_voice_recording_started
        )

        self._handler.subscribe_to_event(
            self._handler.VOICE_RECORDING_STOPPED, self._handle_voice_recording_stopped
        )

        self._handler.subscribe_to_event(
            self._handler.VOICE_OUTPUT_STARTED, self._handle_voice_output_started
        )

        self._handler.subscribe_to_event(
            self._handler.VOICE_OUTPUT_COMPLETED, self._handle_voice_output_completed
        )

        # Animation and UI state events
        self._handler.subscribe_to_event(
            self._handler.ANIMATION_STARTED, self._handle_animation_started
        )

        self._handler.subscribe_to_event(
            self._handler.ANIMATION_STOPPED, self._handle_animation_stopped
        )

        self._handler.subscribe_to_event(
            self._handler.FULLSCREEN_TOGGLED, self._handle_fullscreen_toggled
        )

        # System events
        self._handler.subscribe_to_event(
            self._handler.WARNING_DISPLAYED, self._handle_warning_event
        )

        self._handler.subscribe_to_event(self._handler.ERROR_DISPLAYED, self._handle_error_event)

        self._handler.subscribe_to_event(
            self._handler.SYSTEM_MESSAGE_DISPLAYED, self._handle_system_message_event
        )

        # Audio visualization events
        self._handler.subscribe_to_event(
            self._handler.AUDIO_DATA_UPDATED, self._handle_audio_data_updated
        )

    def _handle_status_event(self, data: Dict[str, Any]) -> None:
        """Handle status update events from UIHandler."""
        if "status" in data:
            self._handle_status_update(data["status"])

    def _handle_user_text_event(self, data: Dict[str, Any]) -> None:
        """Handle user text update events from UIHandler."""
        if "text" in data:
            self._handle_user_text(data["text"])

    def _handle_assistant_text_event(self, data: Dict[str, Any]) -> None:
        """Handle assistant text update events from UIHandler."""
        if "text" in data:
            response_id = data.get("response_id", "")
            self._handle_assistant_text(data["text"], response_id)

    def _handle_warning_event(self, data: Dict[str, Any]) -> None:
        """Handle warning message events from UIHandler."""
        if "text" in data:
            self._handle_warning(data["text"])

    def _handle_error_event(self, data: Dict[str, Any]) -> None:
        """Handle error message events from UIHandler."""
        if "text" in data:
            self._handle_error(data["text"])

    def _handle_system_message_event(self, data: Dict[str, Any]) -> None:
        """Handle system message events from UIHandler."""
        if "text" in data:
            self._handle_system_message(data["text"])

    def _handle_audio_data_updated(self, data: Dict[str, Any]) -> None:
        """Handle audio data update events from UIHandler."""
        if "audio_data" in data:
            self.audio_data = data["audio_data"]
            if self.audio_vis:
                self._run_on_main_thread(lambda: self.audio_vis.set_audio_data(self.audio_data))

    def _handle_voice_recording_started(self, data: Dict[str, Any]) -> None:
        """Handle voice recording started events from UIHandler."""
        if self.record_button:
            self._run_on_main_thread(lambda: self.record_button.update_theme("dangerous"))

    def _handle_voice_recording_stopped(self, data: Dict[str, Any]) -> None:
        """Handle voice recording stopped events from UIHandler."""
        if self.record_button:
            self._run_on_main_thread(lambda: self.record_button.update_theme("default"))

    def _handle_voice_output_started(self, data: Dict[str, Any]) -> None:
        """Handle voice output started events from UIHandler."""
        if "text" in data:
            text = data["text"]
            self._run_on_main_thread(lambda: self._handle_assistant_text(text))

    def _handle_voice_output_completed(self, data: Dict[str, Any]) -> None:
        """Handle voice output completed events from UIHandler."""
        pass

    def _handle_animation_started(self, data: Dict[str, Any]) -> None:
        """Handle animation started events from UIHandler."""
        if "animation_id" not in data:
            return

        animation_id = data["animation_id"]

        # Map animation IDs to UI components
        animation_map = {
            "hexgrid": self.hex_grid,
            "scanline": self.scan_line,
            "progress": self.circle_progress,
            "audio": self.audio_vis,
            "pulse": self.pulse_circle,
        }

        component = animation_map.get(animation_id)
        if component:
            self._run_on_main_thread(component.start)

    def _handle_animation_stopped(self, data: Dict[str, Any]) -> None:
        """Handle animation stopped events from UIHandler."""
        if "animation_id" not in data:
            return

        animation_id = data["animation_id"]

        # Map animation IDs to UI components
        animation_map = {
            "hexgrid": self.hex_grid,
            "scanline": self.scan_line,
            "progress": self.circle_progress,
            "audio": self.audio_vis,
            "pulse": self.pulse_circle,
        }

        component = animation_map.get(animation_id)
        if component:
            self._run_on_main_thread(component.stop)

    def _handle_fullscreen_toggled(self, data: Dict[str, Any]) -> None:
        """Handle fullscreen toggled events from UIHandler."""
        if self.root:
            self._run_on_main_thread(self._toggle_fullscreen)

    def _handle_status_update(self, status: str) -> None:
        """Handle status updates from UIHandler."""
        if self.status_bar:
            self._run_on_main_thread(lambda: self.status_bar.set_status(status))

    def _handle_user_text(self, text: str) -> None:
        """Handle user text updates from UIHandler."""
        if self.text_display:
            self._run_on_main_thread(lambda: self.text_display.add_text(f"User: {text}\n"))

    def _handle_assistant_text(self, text: str, response_id: str = "") -> None:
        """Handle assistant text updates from UIHandler."""
        if self.text_display:
            self._run_on_main_thread(lambda: self.text_display.add_text(f"Assistant: {text}\n"))

    def _handle_voice_command(self, text: str) -> None:
        """Handle voice command from UIHandler."""
        if self.text_display:
            self._run_on_main_thread(lambda: self.text_display.add_text(f"Voice Command: {text}\n"))

    def _handle_theme_change(self, theme: str) -> None:
        """Handle theme change from UIHandler."""
        if theme.lower() == "dangerous" and not self.dangerous:
            self.dangerous = True
            self._run_on_main_thread(self._recreate_ui)
        elif theme.lower() != "dangerous" and self.dangerous:
            self.dangerous = False
            self._run_on_main_thread(self._recreate_ui)

    def _handle_warning(self, text: str) -> None:
        """Handle warning message from UIHandler."""
        if self.text_display:
            self._run_on_main_thread(
                lambda: self.text_display.add_text(f"Warning: {text}\n", "warning")
            )

    def _handle_error(self, text: str) -> None:
        """Handle error message from UIHandler."""
        if self.text_display:
            self._run_on_main_thread(
                lambda: self.text_display.add_text(f"Error: {text}\n", "error")
            )

    def _handle_system_message(self, text: str) -> None:
        """Handle system message from UIHandler."""
        if self.text_display:
            self._run_on_main_thread(lambda: self.text_display.add_text(f"System: {text}\n"))

    def _run_on_main_thread(self, func: Callable[[], Any]) -> None:
        """Run a function on the main thread using the queue."""
        if not self.running:
            return

        self.main_thread_queue.put(func)

    def _process_main_thread_queue(self) -> None:
        """Process the main thread queue."""
        if not self.running:
            return

        try:
            # Process all queued functions
            while not self.main_thread_queue.empty():
                func = self.main_thread_queue.get_nowait()
                func()
        except queue.Empty:
            pass

        # Schedule the next check
        if self.root:
            self.root.after(50, self._process_main_thread_queue)

    def _recreate_ui(self) -> None:
        """Recreate the UI with new theme settings."""
        # Store existing text content
        old_text_content = ""
        if self.text_display:
            old_text_content = self.text_display.get_text()

        # Create new UI
        self._create_ui()

        # Restore text content if needed
        if old_text_content and self.text_display:
            self.text_display.set_text(old_text_content)

    def start(self) -> None:
        """Start the graphical UI."""
        if self.running:
            return

        self.running = True

        # Create and start the main Tkinter loop
        self.root = tk.Tk()
        self._create_ui()

        # Start processing the main thread queue
        self._process_main_thread_queue()

        # Start the UI main loop
        self.root.mainloop()

        # Clean up after main loop exits
        self.running = False

    def _create_ui(self) -> None:
        """Create the UI components."""
        if not self.root:
            return

        # Get theme
        theme = get_theme("dangerous" if self.dangerous else "default")

        # Create UI components
        self.text_display = TextDisplay(self.root, theme)
        self.audio_vis = LiveAudioVisualizer(self.root, theme=theme)
        self.hex_grid = HexagonGrid(self.root, theme=theme)
        self.scan_line = ScanLine(self.root, theme=theme)
        self.circle_progress = CircularProgressAnimation(self.root, theme=theme)
        self.pulse_circle = PulsatingCircle(self.root, theme=theme)
        self.status_bar = StatusBar(self.root, theme)

        # Create record button
        self.record_button = FuturisticButton(
            self.root, text="Record", command=self._handle_voice_toggle, theme=theme
        )

        # Set up initial state
        self._handle_status_update("Online")
        self._handle_assistant_text("AnyRobo interface initialized. How can I assist you?")

    def _handle_voice_toggle(self) -> None:
        """Handle voice toggle button press."""
        self._handler.toggle_voice_recording()

    def _toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        if not self.root:
            return

        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def stop(self) -> None:
        """Stop the graphical UI."""
        self.running = False

        # Close the main window
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None


def run_graphical_ui(
    handler: UIHandler,
    fullscreen: bool = False,
    dangerous: bool = False,
    voice_id: str = "af_heart",
    speech_speed: float = 1.0,
) -> GraphicalUIHandler:
    """
    Run the graphical UI with the specified UIHandler.

    Args:
        handler: The UIHandler to connect with
        fullscreen: Whether to start in fullscreen mode
        dangerous: Whether to use the dangerous theme
        voice_id: Voice ID to use for TTS
        speech_speed: Speech speed multiplier

    Returns:
        The GraphicalUIHandler instance
    """
    # Create and start the UI in a new thread
    handler = GraphicalUIHandler(
        handler,
        fullscreen=fullscreen,
        dangerous=dangerous,
        voice_id=voice_id,
        speech_speed=speech_speed,
    )

    ui_thread = threading.Thread(target=handler.start, daemon=True)
    ui_thread.start()

    return handler
