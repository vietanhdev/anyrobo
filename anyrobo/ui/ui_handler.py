"""
UI Handler for the AnyRobo framework.

Provides a user interface abstraction layer for assistants to interact with
various display and input methods. Supports text, voice, animations, and
themed UI elements.
"""

import tkinter as tk
from tkinter import font
from typing import Optional

from anyrobo.ui import (
    CircularProgressAnimation,
    FuturisticButton,
    HexagonGrid,
    LiveAudioVisualizer,
    ScanLine,
    StatusBar,
    TextDisplay,
    get_theme,
)
from anyrobo.utils.events import Component

# UI Constants
DANGER_RED: str = "#FF3030"
DANGER_ORANGE: str = "#FF7700"
WARNING_YELLOW: str = "#FFDD00"
UI_BLUE: str = "#1E90FF"
UI_LIGHT_BLUE: str = "#87CEFA"
UI_MEDIUM_BLUE: str = "#4682B4"
UI_DARK_BLUE: str = "#0A1F33"
BG_COLOR: str = "#0A192F"


class UIHandler(Component):
    """
    Handles UI interactions for assistants.

    Provides an event-driven interface for displaying and interacting with
    content, independent of the actual UI implementation. Supports text display,
    voice interaction, animations, and UI customization through themes.
    """

    # Event topics for base UI functionality
    STATUS_UPDATED = "ui.status.updated"
    USER_TEXT_UPDATED = "ui.user.text.updated"
    ASSISTANT_TEXT_UPDATED = "ui.assistant.text.updated"
    USER_INPUT_RECEIVED = "ui.user.input.received"
    ACTION_BUTTON_PRESSED = "ui.action.button.pressed"

    # Event topics for voice interaction
    VOICE_RECORDING_STARTED = "ui.voice.recording.started"
    VOICE_RECORDING_STOPPED = "ui.voice.recording.stopped"
    VOICE_COMMAND_RECEIVED = "ui.voice.command.received"
    VOICE_OUTPUT_STARTED = "ui.voice.output.started"
    VOICE_OUTPUT_COMPLETED = "ui.voice.output.completed"

    # Event topics for animations and UI state
    ANIMATION_STARTED = "ui.animation.started"
    ANIMATION_STOPPED = "ui.animation.stopped"
    THEME_CHANGED = "ui.theme.changed"
    FULLSCREEN_TOGGLED = "ui.fullscreen.toggled"

    # Audio visualization events
    AUDIO_DATA_UPDATED = "ui.audio.data.updated"

    # System events
    WARNING_DISPLAYED = "ui.warning.displayed"
    ERROR_DISPLAYED = "ui.error.displayed"
    SYSTEM_MESSAGE_DISPLAYED = "ui.system.message.displayed"

    def __init__(self, root: tk.Tk, theme: str = "default", fullscreen: bool = True) -> None:
        """
        Initialize the UI handler.

        Args:
            root: Root Tkinter window
            theme: Initial UI theme to use
            fullscreen: Whether to start in fullscreen mode
        """
        super().__init__()

        self.root = root
        self.root.title("AnyRobo Assistant")

        # UI state
        self._theme = theme
        self._theme_obj = get_theme(theme)
        self._fullscreen = fullscreen
        self._voice_enabled = False
        self._voice_recording = False
        self._speaking = False

        # Configure root window
        self.root.configure(bg=self._theme_obj.background_color)
        if fullscreen:
            self.root.attributes("-fullscreen", True)
            self.root.bind("<Escape>", self.toggle_fullscreen)
        else:
            self.root.minsize(1024, 768)

        # Configure fonts
        self.setup_fonts()

        # Create main UI components
        self.setup_ui()

        # Start animations
        self.start_animations()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bind resize event
        self.root.bind("<Configure>", self.on_resize)

    def setup_fonts(self) -> None:
        """Setup custom fonts for the UI"""
        self.title_font = font.Font(family="Helvetica", size=28, weight="bold")
        self.text_font = font.Font(family="Courier", size=14)
        self.status_font = font.Font(family="Helvetica", size=11)
        self.button_font = font.Font(family="Helvetica", size=12, weight="bold")

    def setup_ui(self) -> None:
        """Set up the main UI components"""
        # Main frame
        self.main_frame = tk.Frame(self.root, bg=self._theme_obj.background_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create UI elements in proper order
        self.setup_header()

        # Create canvas and animations
        self.create_canvas()
        self.create_animations()

        # Create interactive elements
        self.create_text_display()
        self.create_audio_visualizer()
        self.create_button_panel()
        self.create_status_bar()

    def create_canvas(self) -> None:
        """Create canvas for animations"""
        canvas_frame = tk.Frame(self.main_frame, bg=self._theme_obj.background_color)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            canvas_frame, bg=self._theme_obj.background_color, highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def create_audio_visualizer(self) -> None:
        """Create the audio visualizer component"""
        # LiveAudioVisualizer creates its own frame and canvas when the first parameter is a widget (not a canvas)
        self.audio_vis = LiveAudioVisualizer(
            self.main_frame,  # Pass main_frame as parent - visualizer will create its own canvas
            width=800,
            height=60,
            bars=40,
            theme=self._theme_obj,
        )

    def setup_header(self) -> None:
        """Create the header section with title"""
        header_frame = tk.Frame(self.main_frame, bg=self._theme_obj.background_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = tk.Label(
            header_frame,
            text="AnyRobo Assistant",
            font=self.title_font,
            fg=self._theme_obj.primary_color,
            bg=self._theme_obj.background_color,
        )
        title_label.pack(side=tk.LEFT)

    def create_animations(self) -> None:
        """Create animations on the canvas"""
        canvas_width = self.canvas.winfo_width() or 1024
        canvas_height = self.canvas.winfo_height() or 500

        # Create animations
        self.hex_grid = HexagonGrid(self.canvas, size=30, color=self._theme_obj.primary_color)

        self.scan_line = ScanLine(self.canvas, color=self._theme_obj.accent_color)

        self.circle_progress = CircularProgressAnimation(
            self.canvas,
            int(canvas_width * 0.15),
            int(canvas_height * 0.25),
            size=80,
            color=self._theme_obj.primary_color,
            bg_color=self._theme_obj.background_color,
        )

    def create_text_display(self) -> None:
        """Create the text display area"""
        # Create text display component
        self.text_display = TextDisplay(
            self.main_frame, theme=self._theme_obj, font=self.text_font, height=10
        )
        self.text_display.pack(fill=tk.BOTH, expand=True, pady=20)

    def create_button_panel(self) -> None:
        """Create buttons for interaction"""
        button_frame = tk.Frame(self.main_frame, bg=self._theme_obj.background_color)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Record button
        self.record_button = FuturisticButton(
            button_frame,
            text="START RECORDING",
            command=lambda: self.publish_event(self.ACTION_BUTTON_PRESSED, {"button_id": "record"}),
            theme=self._theme_obj,
            width=180,
            height=40,
            font=self.button_font,
        )
        self.record_button.pack(side=tk.LEFT, padx=(0, 10))

    def create_status_bar(self) -> None:
        """Create the status bar"""
        self.status_bar = StatusBar(
            self.main_frame, theme=self._theme_obj, height=30, font=self.status_font
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

    def start_animations(self) -> None:
        """Start all animations"""
        self.hex_grid.start()
        self.scan_line.start()
        self.circle_progress.start()
        if hasattr(self, "audio_vis") and self.audio_vis is not None:
            self.audio_vis.start()

    def stop_animations(self) -> None:
        """Stop all animations"""
        self.hex_grid.stop()
        self.scan_line.stop()
        self.circle_progress.stop()
        if hasattr(self, "audio_vis") and self.audio_vis is not None:
            self.audio_vis.stop()

    def toggle_fullscreen(self, event: Optional[tk.Event] = None) -> str:
        """Toggle fullscreen mode"""
        self._fullscreen = not self._fullscreen
        self.root.attributes("-fullscreen", self._fullscreen)
        self.publish_event(self.FULLSCREEN_TOGGLED, {"fullscreen": self._fullscreen})
        return "break"

    def on_resize(self, event: tk.Event) -> None:
        """Handle window resize event"""
        # Only handle if it's the root window resizing
        if event.widget == self.root:
            # Wait a bit to make sure the canvas has been resized
            self.root.after(100, self.reposition_animations)

    def reposition_animations(self) -> None:
        """Reposition animations after resize"""
        # Stop animations
        self.stop_animations()

        # Clear canvas
        self.canvas.delete("all")

        # Setup animations with new dimensions
        self.setup_animations()

        # Restart animations
        self.start_animations()

    def on_closing(self) -> None:
        """Handle window closing"""
        # Stop animations
        self.stop_animations()

        # Publish event that UI is closing
        self.publish_event("ui.closing", {})

        # Destroy the root window
        self.root.destroy()

    def add_user_text(self, text: str) -> None:
        """Add user text to the display"""
        self.text_display.add_user_text(text)
        self.publish_event(self.USER_TEXT_UPDATED, {"text": text})

    def add_assistant_text(self, text: str) -> None:
        """Add assistant text to the display"""
        self.text_display.add_system_text(text, "Assistant")
        self.publish_event(self.ASSISTANT_TEXT_UPDATED, {"text": text})

    def set_status(self, text: str) -> None:
        """
        Update the status text with appropriate visual cues.

        Changes the status bar appearance based on status text keywords.

        Args:
            text: Status text to display
        """
        # Define status categories for visual cues
        recording_states = ["Listening", "Recording", "Ready for input"]
        processing_states = ["Processing", "Thinking", "Analyzing"]
        output_states = ["Speaking", "Responding"]
        warning_states = ["Paused", "Waiting"]
        error_states = ["Error", "Failed", "Offline"]

        # Color the status text based on category
        if any(state in text for state in recording_states):
            # Green for recording/listening states
            self.status_bar.set_status(text, color="#00FF00")
        elif any(state in text for state in processing_states):
            # Blue for processing states
            self.status_bar.set_status(text, color="#00AAFF")
        elif any(state in text for state in output_states):
            # Purple for output states
            self.status_bar.set_status(text, color="#AA77FF")
        elif any(state in text for state in warning_states):
            # Yellow for warning states
            self.status_bar.set_warning(text)
        elif any(state in text for state in error_states):
            # Red for error states
            self.status_bar.set_warning(text, error=True)
        else:
            # Default color
            self.status_bar.set_status(text)

        # Publish the status update event
        self.publish_event(self.STATUS_UPDATED, {"text": text})

    def update_record_button_state(self, is_listening: bool) -> None:
        """
        Update record button text and appearance based on listening state.

        Args:
            is_listening: Whether the system is currently listening
        """
        if is_listening:
            self.record_button.set_text("STOP RECORDING")
            self.record_button.set_active(True)
        else:
            self.record_button.set_text("START RECORDING")
            self.record_button.set_active(False)

    def set_warning(self, text: str) -> None:
        """Set warning text in status bar"""
        self.status_bar.set_warning(text, error=False)
        self.publish_event(self.WARNING_DISPLAYED, {"text": text})

    def set_error(self, text: str) -> None:
        """Set error text in status bar"""
        self.status_bar.set_warning(text, error=True)
        self.publish_event(self.ERROR_DISPLAYED, {"text": text})

    def setup_animations(self) -> None:
        """Setup animations based on new dimensions"""
        pass
