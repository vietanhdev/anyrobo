#!/usr/bin/env python3
"""
Simple JARVIS UI Demo

A simplified JARVIS-inspired UI that works with minimal dependencies
"""

import os
import queue
import sys
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import font, ttk

import numpy as np
import sounddevice as sd

# Add the parent directory to sys.path to allow importing anyrobo in development mode
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import AnyRobo components
from anyrobo.models.loader import download_tts_model, ensure_ollama_model
from anyrobo.speech.recognition import SpeechRecognizer
from anyrobo.speech.synthesis import TextToSpeech

# Import UI components from anyrobo.ui
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

# Constants for UI
DANGER_RED = "#FF3030"
DANGER_ORANGE = "#FF7700"
WARNING_YELLOW = "#FFDD00"
UI_BLUE = "#1E90FF"  # Changed from cyan to royal blue
UI_LIGHT_BLUE = "#87CEFA"  # Light sky blue for accents
UI_MEDIUM_BLUE = "#4682B4"  # Steel blue for secondary elements
UI_DARK_BLUE = "#0A1F33"  # Slightly adjusted dark blue
BG_COLOR = "#0A192F"  # Darker blue background

# Set default mode to safe
DEFAULT_DANGEROUS = False


class JarvisUI:
    """JARVIS-inspired UI with animations and text display"""

    def __init__(self, root, fullscreen=True, dangerous=DEFAULT_DANGEROUS):
        self.root = root
        self.root.title("J.A.R.V.I.S - PERSONAL ASSISTANT")

        # Choose theme based on dangerous mode
        self.dangerous = dangerous
        self.theme = get_theme("danger" if dangerous else "jarvis")

        # Apply theme colors to root
        self.root.configure(bg=self.theme.background_color)

        # Fullscreen mode
        self.fullscreen = fullscreen
        if fullscreen:
            self.root.attributes("-fullscreen", True)
            # Bind Escape key to exit fullscreen
            self.root.bind("<Escape>", self.toggle_fullscreen)
        else:
            # Set minimum window size
            self.root.minsize(1024, 768)

        # Configure fonts
        self.setup_fonts()

        # Initialize voice engine
        self.setup_voice_system()

        # Create main frame
        self.main_frame = tk.Frame(root, bg=self.theme.background_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create header with title
        self.create_header()

        # Create canvas for animations
        self.create_animation_canvas()

        # Create text display area
        self.create_text_display()

        # Create button panel
        self.create_button_panel()

        # Create status bar
        self.create_status_bar()

        # Start animations
        self.start_animations()

        # Bind resize event
        self.root.bind("<Configure>", self.on_resize)

        # Voice control state
        self.is_listening = False
        self.audio_buffer = []
        self.audio_queue = queue.Queue()
        self.silence_frames = 0

        # Add lock for processing audio
        self.processing_lock = threading.Lock()
        self.is_processing = False

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Example of adding text after a delay
        self.root.after(1000, self.show_welcome_message)

    def setup_fonts(self):
        """Setup custom fonts for the UI"""
        self.title_font = font.Font(family="Helvetica", size=28, weight="bold")
        self.text_font = font.Font(family="Courier", size=14)
        self.status_font = font.Font(family="Helvetica", size=11)
        self.button_font = font.Font(family="Helvetica", size=12, weight="bold")

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        return "break"

    def create_header(self):
        """Create the header section with title"""
        header_frame = tk.Frame(self.main_frame, bg=self.theme.background_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # Create an alert banner
        alert_frame = tk.Frame(header_frame, bg=self.theme.primary_color, height=30)
        alert_frame.pack(fill=tk.X, pady=(0, 10))

        alert_text = "SECURITY LEVEL: MAXIMUM" if self.dangerous else "ASSISTANT MODE: ACTIVE"
        alert_label = tk.Label(
            alert_frame,
            text=alert_text,
            font=self.status_font,
            fg="white",
            bg=self.theme.primary_color,
        )
        alert_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Blinking classified indicator if dangerous
        if self.dangerous:
            self.classified_label = tk.Label(
                alert_frame,
                text="⚠ CLASSIFIED ⚠",
                font=self.status_font,
                fg="black",
                bg=self.theme.warning_color,
            )
            self.classified_label.pack(side=tk.RIGHT, padx=10, pady=5)
            # Start blinking
            self.blink_classified()

        # Main title
        title_text = "J.A.R.V.I.S COMBAT INTERFACE" if self.dangerous else "J.A.R.V.I.S"
        title_label = tk.Label(
            header_frame,
            text=title_text,
            font=self.title_font,
            fg=self.theme.primary_color,
            bg=self.theme.background_color,
        )
        title_label.pack(side=tk.LEFT)

        subtitle_text = "JUST A RATHER VERY INTELLIGENT SYSTEM"
        subtitle_label = tk.Label(
            header_frame,
            text=subtitle_text,
            font=self.status_font,
            fg=self.theme.secondary_text_color,
            bg=self.theme.background_color,
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=(8, 0))

    def blink_classified(self):
        """Blink the classified indicator"""
        if not hasattr(self, "classified_label"):
            return

        current_bg = self.classified_label.cget("background")
        new_bg = (
            self.theme.warning_color
            if current_bg == self.theme.primary_color
            else self.theme.primary_color
        )
        self.classified_label.config(background=new_bg)
        self.root.after(500, self.blink_classified)

    def create_animation_canvas(self):
        """Create canvas for animations"""
        canvas_frame = tk.Frame(self.main_frame, bg=self.theme.background_color)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=self.theme.background_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Create animations
        self.setup_animations()

    def setup_animations(self):
        """Setup all animations on the canvas"""
        canvas_width = self.canvas.winfo_width() or 1024
        canvas_height = self.canvas.winfo_height() or 500

        # Create hexagonal grid background
        self.hex_grid = HexagonGrid(self.canvas, size=30, color=self.theme.primary_color)

        # Create scan line
        self.scan_line = ScanLine(self.canvas, color=self.theme.accent_color)

        # Circular progress animation (top-left)
        self.circle_progress = CircularProgressAnimation(
            self.canvas,
            canvas_width * 0.15,
            canvas_height * 0.25,
            size=80,
            color=self.theme.primary_color,
            bg_color=self.theme.background_color,
        )

        # Audio visualizer (bottom)
        self.audio_vis = LiveAudioVisualizer(
            self.canvas,
            canvas_width * 0.5,
            canvas_height * 0.85,
            width=canvas_width * 0.7,
            height=50,
            bars=40,
            color=self.theme.primary_color,
        )

        # Add text and decorative elements
        status_text = "WEAPONS ONLINE" if self.dangerous else "SYSTEMS ONLINE"
        self.status_text = self.canvas.create_text(
            canvas_width * 0.5,
            canvas_height * 0.5,
            text=status_text,
            fill=self.theme.primary_color,
            font=self.title_font,
        )

        # Add timestamp and coordinates for military feel
        coords_text = "LAT: 37.7749° N | LON: 122.4194° W | ALT: 52m"
        self.coords_text = self.canvas.create_text(
            canvas_width * 0.85,
            canvas_height * 0.95,
            text=coords_text,
            fill=self.theme.secondary_color,
            font=self.status_font,
            anchor="se",
        )

    def start_animations(self):
        """Start all animations"""
        self.hex_grid.start()
        self.scan_line.start()
        self.circle_progress.start()
        self.audio_vis.start()

    def stop_animations(self):
        """Stop all animations"""
        self.hex_grid.stop()
        self.scan_line.stop()
        self.circle_progress.stop()
        self.audio_vis.stop()

    def create_text_display(self):
        """Create the text display area"""
        # Use TextDisplay component from the UI module
        self.text_display_component = TextDisplay(
            self.main_frame, theme=self.theme, font=self.text_font, height=10
        )
        self.text_display_component.pack(fill=tk.BOTH, expand=True, pady=20)

        # Set text display reference for easy access
        self.text_display = self.text_display_component.text
        
        # Set up scrolling variables
        self.auto_scroll_enabled = True  # Flag to control auto-scrolling
        self.user_scrolled = False  # Track if user manually scrolled
        
        # Add scroll event bindings
        self.text_display.bind("<MouseWheel>", self._on_user_scroll)  # Windows
        self.text_display.bind("<Button-4>", self._on_user_scroll)  # Linux scroll up
        self.text_display.bind("<Button-5>", self._on_user_scroll)  # Linux scroll down
        
        # Initial scroll to end
        self.text_display.see(tk.END)
        
        # Set up smooth auto-scroll
        self._setup_smooth_auto_scroll()

        # Add some initial text
        self.add_jarvis_text("JARVIS interface initialized. Awaiting instructions.")
        if self.dangerous:
            self.text_display_component.add_text(
                "WARNING: Combat mode activated. Weapon systems online.", "warning"
            )

    def _on_user_scroll(self, event):
        """Detect when user manually scrolls"""
        # Get current scroll position
        y_view = self.text_display.yview()
        
        # If user scrolls away from bottom, disable auto-scroll
        if y_view[1] < 0.99:
            self.user_scrolled = True
            self.auto_scroll_enabled = False
        
        # If user scrolls to bottom, re-enable auto-scroll
        elif y_view[1] >= 0.99:
            self.user_scrolled = False
            self.auto_scroll_enabled = True
            
        # Let the event propagate
        return

    def _setup_smooth_auto_scroll(self):
        """Set up smoother automatic scrolling functionality"""
        def smooth_scroll_to_bottom():
            if not hasattr(self, 'text_display') or not self.text_display.winfo_exists():
                return  # Widget doesn't exist anymore
                
            try:
                # Check if auto-scroll is enabled
                if self.auto_scroll_enabled:
                    # Get current position
                    y_view = self.text_display.yview()
                    
                    # If we're already at the bottom, just maintain
                    if y_view[1] >= 0.99:
                        self.text_display.see(tk.END)
                    # Otherwise do a smooth scroll
                    else:
                        # Calculate a step size for smooth scrolling
                        current_pos = y_view[0]
                        target_pos = 1.0  # Bottom of text
                        step = min(0.05, (target_pos - current_pos) / 3)  # Smaller of 0.05 or 1/3 of distance
                        
                        if step > 0.001:  # Only move if significant change
                            # Move incrementally toward bottom
                            new_pos = current_pos + step
                            self.text_display.yview_moveto(new_pos)
                
                # Continue scrolling
                self.root.after(16, smooth_scroll_to_bottom)  # ~60fps for smooth animation
                
            except Exception as e:
                print(f"Smooth scroll error: {e}")
                # Try again after a short delay
                self.root.after(100, smooth_scroll_to_bottom)
        
        # Start smooth scrolling loop
        self.root.after(16, smooth_scroll_to_bottom)

    def create_button_panel(self):
        """Create buttons for interaction"""
        button_frame = tk.Frame(self.main_frame, bg=self.theme.background_color)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # Voice button (always visible if voice system is available)
        if hasattr(self, "voice_available") and self.voice_available:
            self.voice_button = FuturisticButton(
                button_frame,
                text="START VOICE INPUT",
                command=self.toggle_listening,
                theme=self.theme,
                width=180,
                height=40,
                font=self.button_font,
            )
            self.voice_button.pack(side=tk.LEFT, padx=(0, 10))

        # Status button
        self.status_button = FuturisticButton(
            button_frame,
            text="SYSTEM STATUS",
            command=self.show_status,
            theme=self.theme,
            width=180,
            height=40,
            font=self.button_font,
        )
        self.status_button.pack(side=tk.LEFT, padx=(0, 10))

        if not self.dangerous:
            # Add assistant buttons for non-dangerous mode
            self.weather_button = FuturisticButton(
                button_frame,
                text="WEATHER",
                command=self.show_weather,
                theme=self.theme,
                width=140,
                height=40,
                font=self.button_font,
            )
            self.weather_button.pack(side=tk.LEFT, padx=(0, 10))

            self.calendar_button = FuturisticButton(
                button_frame,
                text="CALENDAR",
                command=self.show_calendar,
                theme=self.theme,
                width=140,
                height=40,
                font=self.button_font,
            )
            self.calendar_button.pack(side=tk.LEFT, padx=(0, 10))

        # Alert button if dangerous
        if self.dangerous:
            self.alert_button = FuturisticButton(
                button_frame,
                text="ACTIVATE ALERT",
                command=self.toggle_alert,
                theme=self.theme,
                width=180,
                height=40,
                font=self.button_font,
            )
            self.alert_button.pack(side=tk.LEFT, padx=(0, 10))
            self.alert_active = False

    def show_status(self):
        """Show system status information"""
        status_text = (
            (
                "COMBAT SYSTEMS:\n"
                "- Weapons: ONLINE\n"
                "- Defense shields: 98% CAPACITY\n"
                "- Targeting systems: CALIBRATED\n"
                "- Threat assessment: ACTIVE\n"
            )
            if self.dangerous
            else (
                "SYSTEM STATUS:\n"
                "- Core functions: NORMAL\n"
                "- Power systems: 98% EFFICIENCY\n"
                "- Environmental systems: OPTIMAL\n"
                "- Network connectivity: SECURE\n"
            )
        )

        self.add_jarvis_text(status_text)

    def toggle_alert(self):
        """Toggle alert state"""
        if hasattr(self, "alert_active") and hasattr(self, "alert_button"):
            self.alert_active = not self.alert_active

            if self.alert_active:
                self.alert_button.update_theme("danger")
                self.status_bar.set_warning("ALERT ACTIVE - SECURITY BREACH DETECTED")
                self.text_display_component.add_text(
                    "WARNING: Security protocols engaged. Unauthorized access detected.", "warning"
                )
            else:
                self.alert_button.update_theme(self.theme)
                self.status_bar.set_warning("")
                self.text_display_component.add_text(
                    "Alert deactivated. Security status normalized.", "system"
                )

    def create_status_bar(self):
        """Create the status bar at the bottom"""
        # Use StatusBar component from the UI module
        self.status_bar = StatusBar(
            self.main_frame, theme=self.theme, height=30, font=self.status_font
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

        # Update clock is handled by the StatusBar component

    def add_jarvis_text(self, text):
        """Add text from JARVIS to the display"""
        self.text_display_component.add_system_text(text, "JARVIS")
        # Re-enable auto-scrolling when system adds text
        self.auto_scroll_enabled = True

    def add_user_text(self, text):
        """Add user text to the display"""
        self.text_display_component.add_user_text(text)
        # Re-enable auto-scrolling when user text is added
        self.auto_scroll_enabled = True

    def add_text(self, text, tag=None):
        """Add text with optional formatting"""
        self.text_display_component.add_text(text, tag)
        # Re-enable auto-scrolling when text is added
        self.auto_scroll_enabled = True

    def set_status(self, text):
        """Update the status text"""
        self.status_bar.set_status(text)

    def set_warning(self, text):
        """Set warning text in status bar"""
        self.status_bar.set_warning(text)

    def on_resize(self, event):
        """Handle window resize event"""
        # Only handle if it's the root window resizing
        if event.widget == self.root:
            # Wait a bit to make sure the canvas has been resized
            self.root.after(100, self.reposition_animations)

    def reposition_animations(self):
        """Reposition animations after resize"""
        # Stop animations
        self.stop_animations()

        # Clear canvas
        self.canvas.delete("all")

        # Setup animations with new dimensions
        self.setup_animations()

        # Restart animations
        self.start_animations()

    def show_weather(self):
        """Show weather information"""
        weather_text = (
            "CURRENT WEATHER:\n"
            "- Temperature: 72°F / 22°C\n"
            "- Conditions: Clear skies\n"
            "- Humidity: 45%\n"
            "- Wind: 5 mph NW\n\n"
            "FORECAST:\n"
            "- Today: Sunny, high of 75°F\n"
            "- Tomorrow: Partly cloudy, high of 73°F"
        )
        self.add_jarvis_text(weather_text)

    def show_calendar(self):
        """Show calendar information"""
        today = time.strftime("%A, %B %d")
        calendar_text = (
            f"TODAY'S SCHEDULE ({today}):\n"
            "- 9:00 AM: Team meeting\n"
            "- 12:00 PM: Lunch with Sarah\n"
            "- 2:30 PM: Project review\n"
            "- 5:00 PM: Gym\n\n"
            "UPCOMING EVENTS:\n"
            "- Tomorrow: Dinner reservation at 7:00 PM\n"
            "- Saturday: Movie night at 8:00 PM"
        )
        self.add_jarvis_text(calendar_text)

    def setup_voice_system(self):
        """Initialize the voice system components"""
        try:
            # Download required models without unsupported parameters
            download_tts_model()  # TTS model
            ensure_ollama_model("llama3.2")  # LLM
            
            # Speech settings
            self.sample_rate = 24000
            self.silence_threshold = 0.01  # Lower threshold to better detect quiet speech
            self.silence_duration = 2.0  # Increase duration to allow longer pauses
            self.voice = "am_michael"  # Using a masculine voice for JARVIS
            self.speed = 1.2
            
            # TTS optimization settings
            self.tts_chunk_size = 40  # Process smaller chunks for faster response
            self.max_queued_chunks = 3  # Don't queue too many chunks ahead
            
            # System prompt for JARVIS personality
            self.system_prompt = (
                "You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), "
                "the advanced AI assistant created by Tony Stark. "
                "You have a British accent, dry wit, and immense technical knowledge. "
                "You are polite, efficient, and occasionally sarcastic. "
                "Your responses should be concise, intelligent, and slightly playful. "
                "You often address the user as 'sir' or 'madam' and have a subtle sense of humor. "
                "IMPORTANT: Keep your responses extremely brief and to the point. Use at most 1-3 short sentences. "
                "Avoid unnecessary explanations, pleasantries or verbosity. Prioritize delivering information "
                "in the most direct way possible while maintaining your personality."
            )
            
            # Initialize components with optimized settings
            self.speech_recognizer = SpeechRecognizer(model="small", batch_size=12)
            self.tts = TextToSpeech()  # Use default settings (no quantized parameter)
            
            # Audio sequencing
            self.tts_queue = queue.Queue()  # Queue for TTS chunks
            self.tts_playing = False
            self.tts_sequence_number = 0  # For ordering audio chunks
            self.pending_audio_chunks = {}  # Store chunks by sequence number
            
            # Audio thread control
            self.tts_thread_active = True
            self.executor = ThreadPoolExecutor(max_workers=2)
            
            # Start TTS player thread
            self.tts_thread = threading.Thread(target=self._tts_player_thread, daemon=True)
            self.tts_thread.start()
            
            # Chat history
            self.messages = []
            
            # Set voice system as available
            self.voice_available = True
            print("Voice system initialized successfully with optimized settings")
            
        except Exception as e:
            print(f"Failed to initialize voice system: {e}")
            self.voice_available = False

    def _tts_player_thread(self):
        """Background thread that plays TTS audio as it becomes available"""
        try:
            next_chunk_to_play = 0  # Next sequence number to play
            
            while self.tts_thread_active:
                # Check if we have the next chunk in our pending dictionary
                if next_chunk_to_play in self.pending_audio_chunks:
                    # Get the audio chunk with the current sequence number
                    audio_chunk = self.pending_audio_chunks.pop(next_chunk_to_play)
                    
                    # Set playing flag
                    self.tts_playing = True
                    
                    # Update UI to show speaking state
                    self.root.after(0, lambda: self.set_status("Speaking"))
                    
                    # Temporarily pause audio input if we're listening
                    was_listening = False
                    if hasattr(self, 'is_listening') and self.is_listening:
                        was_listening = True
                        self.root.after(0, self.pause_listening)
                    
                    try:
                        # Play the audio
                        with sd.OutputStream(
                            samplerate=self.sample_rate,
                            channels=1,
                            dtype=np.float32,
                            blocksize=4096  # Larger blocksize for smoother playback
                        ) as stream:
                            stream.write(audio_chunk.reshape(-1, 1))
                    except Exception as e:
                        print(f"Error playing audio chunk {next_chunk_to_play}: {e}")
                    
                    # Increment for next chunk
                    next_chunk_to_play += 1
                    
                    # Clear playing flag if no more chunks
                    if len(self.pending_audio_chunks) == 0:
                        self.tts_playing = False
                        # Resume listening if it was active before
                        if was_listening:
                            self.root.after(0, self.resume_listening)
                else:
                    # No chunk available yet, wait a bit
                    time.sleep(0.05)
                    
                    # If we've been waiting for new chunks and the queue is empty,
                    # check if we should reset the sequence counter
                    if (not self.tts_playing and 
                        len(self.pending_audio_chunks) == 0 and 
                        self.tts_queue.empty()):
                        next_chunk_to_play = 0  # Reset for next session
                        time.sleep(0.1)  # Avoid busy waiting
        
        except Exception as e:
            print(f"Error in TTS player thread: {e}")
            self.tts_playing = False
    
    def _process_tts_chunk(self, text, voice, speed, seq_num):
        """Process a TTS chunk and add to playback queue with sequence number"""
        try:
            if not text.strip():
                return
                
            audio_data = self.tts.generate_audio(text, voice, speed)
            if len(audio_data) > 0:
                # Store with sequence number for ordered playback
                self.pending_audio_chunks[seq_num] = audio_data
        except Exception as e:
            print(f"Error generating TTS audio for chunk {seq_num}: {e}")

    def pause_listening(self):
        """Temporarily pause audio input without changing UI state"""
        if hasattr(self, 'is_listening') and self.is_listening:
            self.is_listening_paused = True
            # Show visual indicator that listening is paused during speech
            self.set_status("Speaking (input paused)")
            if hasattr(self, 'voice_button'):
                self.voice_button.update_theme('default')
                self.voice_button.canvas.itemconfig(
                    self.voice_button.button_text, text="INPUT PAUSED"
                )
    
    def resume_listening(self):
        """Resume audio input if it was paused"""
        if hasattr(self, 'is_listening_paused') and self.is_listening_paused:
            self.is_listening_paused = False
            if self.is_listening:
                self.set_status("Listening")
                if hasattr(self, 'voice_button'):
                    self.voice_button.update_theme('danger' if not self.dangerous else 'default')
                    self.voice_button.canvas.itemconfig(
                        self.voice_button.button_text, text="STOP VOICE INPUT"
                    )
                    
    def start_listening(self):
        """Start listening for voice input"""
        if self.is_listening:
            return
            
        # Don't start listening if TTS is playing
        if hasattr(self, 'tts_playing') and self.tts_playing:
            self.add_text("Cannot start voice input while JARVIS is speaking.", "warning")
            return
            
        self.is_listening = True
        self.is_listening_paused = False
        
        # Update UI
        if hasattr(self, 'voice_button'):
            self.voice_button.update_theme('danger' if not self.dangerous else 'default')
            # Update text directly since we can't change the button text easily
            self.voice_button.canvas.itemconfig(self.voice_button.button_text, text="STOP VOICE INPUT")
        
        self.set_status("Listening")
        self.add_text("Voice recognition activated. Speak now...", "system")
        
        # Reset audio buffer and counters
        self.audio_buffer = []
        self.silence_frames = 0
        
        # Start audio stream in a separate thread
        threading.Thread(target=self._listen_for_audio, daemon=True).start()

    def _listen_for_audio(self):
        """Listen for audio input and process it"""
        try:
            # Tracking variables for better silence detection
            self.audio_data_being_captured = False
            last_active_time = time.time()
            min_recording_time = 1.0  # Minimum recording time in seconds
                
            def audio_callback(indata, frames, time_info, status):
                """Callback for audio stream"""
                nonlocal last_active_time
                
                if not self.is_listening:
                    raise sd.CallbackStop
                
                # Skip processing if TTS is playing or listening is paused
                if hasattr(self, 'tts_playing') and self.tts_playing:
                    return
                
                if hasattr(self, 'is_listening_paused') and self.is_listening_paused:
                    return
                
                if status:
                    print(f"Audio status: {status}")
                
                # Get audio data and calculate volume level
                audio = indata.flatten()
                level = np.abs(audio).mean()
                
                # Add to buffer (always capture data)
                self.audio_buffer.extend(audio.tolist())
                
                # Update visualizer if it exists
                if hasattr(self, 'audio_vis') and isinstance(self.audio_vis, LiveAudioVisualizer):
                    # Scale audio to make bars visible
                    scaled_audio = audio * 5
                    self.audio_vis.set_audio_data(scaled_audio)
                
                # Detect speech activity
                if level >= self.silence_threshold:
                    # Active speech detected
                    self.audio_data_being_captured = True
                    last_active_time = time.time()
                    self.silence_frames = 0
                else:
                    # Count silent frames only if we're recording
                    if self.audio_data_being_captured:
                        self.silence_frames += len(audio)
                
                # Process audio when:
                # 1. We have active speech and
                # 2. We detect an extended silence after speech and
                # 3. We've been recording for at least the minimum time
                current_time = time.time()
                recording_duration = current_time - last_active_time
                
                if (self.audio_data_being_captured and 
                    self.silence_frames > self.silence_duration * self.sample_rate and
                    len(self.audio_buffer) > self.sample_rate * min_recording_time):
                    
                    # Create a copy to avoid race conditions
                    audio_segment = np.array(self.audio_buffer, dtype=np.float32)
                    
                    # Only process significant audio
                    if len(audio_segment) > self.sample_rate:
                        # Process in main thread to avoid threading issues
                        self.root.after(0, lambda a=audio_segment: self._process_audio(a))
                    
                    # Reset state
                    self.audio_buffer = []
                    self.silence_frames = 0
                    self.audio_data_being_captured = False
            
            # Start audio stream
            with sd.InputStream(
                callback=audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                dtype=np.float32,
                blocksize=int(0.05 * self.sample_rate)  # 50ms blocks for more responsive detection
            ):
                # Keep running until stopped
                while self.is_listening:
                    sd.sleep(100)
                    
        except Exception as e:
            print(f"Error in audio listening: {e}")
            self.root.after(0, lambda: self.add_text(f"Audio error: {str(e)}", "error"))
            self.root.after(0, self.stop_listening)

    def _process_audio(self, audio_segment):
        """Process recorded audio segment"""
        if not self.is_listening:
            return
            
        # Skip if TTS is playing or listening is paused
        if hasattr(self, 'tts_playing') and self.tts_playing:
            return
            
        if hasattr(self, 'is_listening_paused') and self.is_listening_paused:
            return

        # Use a lock to prevent multiple processing at the same time
        if self.is_processing:
            print("Already processing audio, skipping...")
            return

        try:
            # Acquire lock to prevent multiple responses
            with self.processing_lock:
                if self.is_processing:
                    return
                self.is_processing = True

            # Show processing status
            self.set_status("Processing")

            # Transcribe audio
            result = self.speech_recognizer.transcribe(audio_segment)
            text = result.get("text", "").strip()

            # Skip empty/invalid transcriptions
            if not text:
                self.set_status("Listening")
                self.is_processing = False
                return

            # Show transcription
            self.add_user_text(text)

            # Add to chat history
            self.messages.append({"role": "user", "content": text})

            # Generate and show response
            self.generate_response()

        except Exception as e:
            print(f"Error processing audio: {e}")
            self.add_text(f"Error processing speech: {str(e)}", "error")
            self.is_processing = False

        finally:
            # Reset status if still listening
            if self.is_listening:
                self.set_status("Listening")

    def generate_response(self):
        """Generate a response using the LLM and TTS"""
        if not hasattr(self, "voice_available") or not self.voice_available:
            return

        try:
            # Set status
            self.set_status("Thinking")

            # Start response generation in a separate thread
            threading.Thread(target=self._generate_and_speak_response, daemon=True).start()

        except Exception as e:
            print(f"Error generating response: {e}")
            self.add_text(f"Error generating response: {str(e)}", "error")
            self.set_status("Online")
            
    def _generate_and_speak_response(self):
        """Generate and speak a response based on chat history"""
        try:
            from ollama import chat
            import re  # For improved sentence detection
            
            # Generate response
            stream = chat(
                model='llama3.2',
                messages=[{
                    'role': 'system',
                    'content': self.system_prompt
                }] + self.messages,
                stream=True,
            )
            
            # State for processing response
            buffer = ""
            complete_response = ""
            tts_futures = []
            
            # For ordered audio processing
            current_seq = 0
            playback_started = False
            last_update_time = time.time()
            
            # Reset sequence counter for new response
            self.tts_sequence_number = 0
            
            # Create a unique response ID for this response session
            self.current_response_id = f"response_{time.time()}"
            
            # Add initial placeholder for streaming response - use main thread and wait for it
            self.root.after(0, lambda: self._add_initial_response_placeholder(self.current_response_id))
            # Give UI time to update
            time.sleep(0.2)
            
            # Add visible "Generating response..." indicator
            self.set_status("Generating response")
            
            # Clear any pending audio chunks from previous responses
            self.pending_audio_chunks.clear()
            
            # Pattern for sentence boundaries - matches sentence ending punctuation followed by space or end of string
            sentence_pattern = re.compile(r'([.!?])\s+|([.!?])$')
            
            # Process response stream
            for chunk in stream:
                if not hasattr(self, 'root'):
                    break
                    
                text = chunk['message']['content']
                
                if len(text) == 0:
                    # End of response
                    if complete_response:
                        self.messages.append({
                            'role': 'assistant',
                            'content': complete_response
                        })
                    break
                
                # Add to buffers
                buffer += text
                complete_response += text
                
                # Update UI with partial response
                current_time = time.time()
                if current_time - last_update_time > 0.1:  # Update at most 10 times per second
                    self.root.after(0, lambda r=complete_response, id=self.current_response_id: 
                                self._update_response_text(r, id))
                    last_update_time = current_time
                    # Small sleep to give UI time to update
                    time.sleep(0.01)
                
                # Check for complete sentences in the buffer
                sentences = []
                last_end = 0
                
                # Find all sentence boundaries in the current buffer
                for match in sentence_pattern.finditer(buffer):
                    end_pos = match.end()
                    sentence = buffer[last_end:end_pos].strip()
                    if sentence:  # Only add non-empty sentences
                        sentences.append(sentence)
                    last_end = end_pos
                
                # Process complete sentences for TTS
                if sentences:
                    # Get remaining text after last sentence
                    remaining = buffer[last_end:].strip()
                    
                    # Process each complete sentence as a TTS chunk
                    for sentence in sentences:
                        # Get sequence number for this chunk
                        seq_num = self.tts_sequence_number
                        self.tts_sequence_number += 1
                        
                        # First sentence - process immediately for fast response
                        if not playback_started and current_seq == 0:
                            try:
                                audio_data = self.tts.generate_audio(sentence, self.voice, self.speed)
                                if len(audio_data) > 0:
                                    self.pending_audio_chunks[seq_num] = audio_data
                                    playback_started = True
                            except Exception as e:
                                print(f"Error generating first audio chunk: {e}")
                        else:
                            # Submit remaining sentences for background processing
                            tts_futures.append(
                                self.executor.submit(
                                    self._process_tts_chunk, 
                                    sentence, 
                                    self.voice, 
                                    self.speed,
                                    seq_num
                                )
                            )
                        
                        current_seq += 1
                    
                    # Update buffer to only contain the remaining text
                    buffer = remaining
                
                # Check if buffer is getting too large without sentence boundaries
                # This prevents growing the buffer indefinitely if no sentence endings are found
                if len(buffer) > self.tts_chunk_size * 2:
                    # Look for any reasonable break point (comma, semicolon, etc.)
                    break_pattern = re.compile(r'([,;:])\s+|(\s+and\s+|\s+or\s+|\s+but\s+)')
                    break_match = list(break_pattern.finditer(buffer))
                    
                    if break_match:
                        # Use the last good break point
                        last_break = break_match[-1]
                        break_pos = last_break.end()
                        
                        chunk_text = buffer[:break_pos].strip()
                        buffer = buffer[break_pos:].strip()
                        
                        # Only process if we have meaningful text
                        if chunk_text:
                            seq_num = self.tts_sequence_number
                            self.tts_sequence_number += 1
                            
                            tts_futures.append(
                                self.executor.submit(
                                    self._process_tts_chunk, 
                                    chunk_text, 
                                    self.voice, 
                                    self.speed,
                                    seq_num
                                )
                            )
                            current_seq += 1
                    elif len(buffer) > self.tts_chunk_size * 3:
                        # If no break points found and buffer is very large, 
                        # force a break at a word boundary as last resort
                        words = buffer.split()
                        if len(words) > 10:  # Ensure we have enough words
                            # Take first 60% of words
                            word_break = int(len(words) * 0.6)
                            chunk_text = " ".join(words[:word_break])
                            buffer = " ".join(words[word_break:])
                            
                            seq_num = self.tts_sequence_number
                            self.tts_sequence_number += 1
                            
                            tts_futures.append(
                                self.executor.submit(
                                    self._process_tts_chunk, 
                                    chunk_text, 
                                    self.voice, 
                                    self.speed,
                                    seq_num
                                )
                            )
                            current_seq += 1
                
                # Wait for some futures to complete if we have too many to avoid memory issues
                if len(tts_futures) > self.max_queued_chunks * 2:
                    done_futures = []
                    for i, future in enumerate(tts_futures):
                        if future.done():
                            done_futures.append(i)
                    
                    # Remove completed futures (in reverse to avoid index issues)
                    for i in sorted(done_futures, reverse=True):
                        tts_futures.pop(i)
            
            # Final update for any remaining text
            if time.time() - last_update_time > 0.05:
                self.root.after(0, lambda r=complete_response, id=self.current_response_id: 
                            self._update_response_text(r, id))
                time.sleep(0.05)
            
            # Process final chunk if any remaining text in buffer
            if buffer:
                seq_num = self.tts_sequence_number
                self.tts_sequence_number += 1
                tts_futures.append(
                    self.executor.submit(
                        self._process_tts_chunk,
                        buffer,
                        self.voice,
                        self.speed,
                        seq_num
                    )
                )
            
            # Wait for all futures to complete (not their results)
            for future in tts_futures:
                try:
                    future.result(timeout=5.0)  # Add timeout to avoid hanging
                except Exception as e:
                    print(f"Error waiting for TTS future: {e}")
            
            # Make sure we got text, otherwise show an error message
            if not complete_response:
                self.root.after(0, lambda: self.add_text("I'm sorry, I couldn't generate a response. Please try again.", "error"))
                self.root.after(0, lambda: self.set_status("Online"))
                self.is_processing = False
                return
                
            # Update UI with complete response - use main thread
            self.root.after(0, lambda resp=complete_response, rid=self.current_response_id: 
                           self._finalize_response(resp, rid))
            time.sleep(0.1)  # Give UI time to update
            
        except Exception as e:
            print(f"Error in response generation: {e}")
            # Use traceback to get full error details
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.add_text(f"Error generating response: {str(e)}", "error"))
            self.root.after(0, lambda: self.set_status("Online"))
        finally:
            # Reset processing flag after response generation completes
            self.is_processing = False

    def _add_initial_response_placeholder(self, response_id):
        """Add initial placeholder for the streaming response"""
        try:
            # Direct approach to add text - simpler and more reliable
            # Create a new entry in the text display
            self.text_display.config(state=tk.NORMAL)
            
            # Clear any existing placeholder (rare race condition)
            if hasattr(self, 'current_response_line'):
                try:
                    line_start = self.current_response_line
                    line_end = f"{line_start} lineend+1c"  # Include newline
                    self.text_display.delete(line_start, line_end)
                except:
                    pass  # Ignore if the deletion fails
            
            # Add the JARVIS prefix with system tag
            jarvis_prefix = "JARVIS: "
            self.text_display.insert(tk.END, jarvis_prefix, "system")
            
            # Store the last line position for updating
            self.current_response_line = self.text_display.index(tk.END + "-1c linestart")
            self.current_response_prefix_length = len(jarvis_prefix)
            
            # Create a unique tag for this response for tracking
            tag_name = f"response_{response_id}"
            self.text_display.tag_add(tag_name, f"{self.current_response_line} linestart", f"{self.current_response_line} lineend")
            
            # Make sure we can see the insertion point
            self.text_display.see(tk.END)
            self.text_display.config(state=tk.DISABLED)
            
            # Force update to ensure UI refreshes
            self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error creating response placeholder: {e}")
            # Fallback direct text display
            self.add_text(f"JARVIS is thinking...", "system")
    
    def _update_response_text(self, partial_response, response_id):
        """Update the UI with a partial response"""
        try:
            # Simple direct approach to replace text
            if hasattr(self, 'current_response_line'):
                # Calculate position after JARVIS: prefix
                prefix_length = getattr(self, 'current_response_prefix_length', 8)  # Default to 8 if not set
                prefix_pos = f"{self.current_response_line} + {prefix_length}c"  # chars for prefix
                
                # Open text for editing
                self.text_display.config(state=tk.NORMAL)
                
                # Check if we need to delete existing content
                if self.text_display.get(prefix_pos, f"{self.current_response_line} lineend") != "":
                    # Clear from after prefix to end of line
                    line_end = f"{self.current_response_line} lineend"
                    self.text_display.delete(prefix_pos, line_end)
                
                # Insert updated text
                self.text_display.insert(prefix_pos, partial_response)
                
                # Make sure we can see it
                self.text_display.see(tk.END)
                
                # Protect text again
                self.text_display.config(state=tk.DISABLED)
                
                # Force immediate visual update
                self.root.update_idletasks()
            else:
                # Fallback - direct display without position info
                print("Warning: No position information for response update, using direct method")
                # Add the response as new text - last resort
                self.text_display.config(state=tk.NORMAL)
                # Find and delete any existing partial response line at the end
                last_line = self.text_display.get("end-2l", "end-1c")
                if last_line.startswith("JARVIS: "):
                    self.text_display.delete("end-2l", "end-1c")
                
                self.text_display.insert(tk.END, f"JARVIS: {partial_response}\n", "system")
                self.text_display.see(tk.END)
                self.text_display.config(state=tk.DISABLED)
                self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error updating response text: {e}")
            # Last resort - completely direct method
            try:
                self.add_text(f"JARVIS: {partial_response}", "system")
            except:
                print("Failed all text display methods")
    
    def _finalize_response(self, response, response_id):
        """Finalize the response display"""
        try:
            if hasattr(self, 'current_response_line'):
                # Calculate position after JARVIS: prefix
                prefix_length = getattr(self, 'current_response_prefix_length', 8)  # Default to 8 if not set
                prefix_pos = f"{self.current_response_line} + {prefix_length}c"  # chars for prefix
                
                # Open text for editing
                self.text_display.config(state=tk.NORMAL)
                
                # Clear from after prefix to end of line
                line_end = f"{self.current_response_line} lineend"
                self.text_display.delete(prefix_pos, line_end)
                
                # Insert updated text and add newlines to prepare for next message
                self.text_display.insert(prefix_pos, f"{response}\n\n")
                
                # Make sure we can see it
                self.text_display.see(tk.END)
                
                # Protect text again
                self.text_display.config(state=tk.DISABLED)
                
                # Clear the current line reference
                delattr(self, 'current_response_line')
                if hasattr(self, 'current_response_prefix_length'):
                    delattr(self, 'current_response_prefix_length')
                
                # Force immediate visual update
                self.root.update_idletasks()
            else:
                # Fallback - display without position info
                print("Warning: No position information for finalizing response, using direct method")
                # Simple method to add complete text
                self.add_jarvis_text(f"{response}")
                self.root.update_idletasks()
            
        except Exception as e:
            print(f"Error finalizing response: {e}")
            # Last resort if all else fails
            try:
                self.add_jarvis_text(response)
            except:
                print("Failed all text display methods")
        
        # Reset status if we're still listening
        if self.is_listening and not self.tts_playing:
            self.set_status("Listening")
        elif not self.is_listening:
            self.set_status("Online")

    def show_welcome_message(self):
        """Show welcome message with delayed display"""
        greeting = "Good " + (
            "morning"
            if 5 <= time.localtime().tm_hour < 12
            else "afternoon"
            if 12 <= time.localtime().tm_hour < 18
            else "evening"
        )

        welcome_msg = f"{greeting}. All systems are functioning at optimal levels."
        self.add_jarvis_text(welcome_msg)

        # Also speak the welcome message if voice is available
        if hasattr(self, "voice_available") and self.voice_available:
            try:
                audio_data = self.tts.generate_audio(welcome_msg, self.voice, self.speed)
                sd.play(audio_data, self.sample_rate)
            except Exception as e:
                print(f"Error playing welcome audio: {e}")

        # Schedule the next message
        self.root.after(2000, self.show_second_message)

    def show_second_message(self):
        """Show the second welcome message"""
        if self.dangerous:
            self.set_warning("COMBAT PROTOCOLS ACTIVE")
            self.add_text("WARNING: Unauthorized access detected in sector 7-G", "warning")
            self.root.after(
                1500,
                lambda: self.add_jarvis_text(
                    "Security breach contained. Defensive protocols engaged."
                ),
            )
        else:
            current_time = time.strftime("%H:%M")
            current_date = time.strftime("%A, %B %d, %Y")
            time_msg = f"The current time is {current_time}. Today is {current_date}."
            self.add_jarvis_text(time_msg)

            self.root.after(1500, self.show_help_message)

    def show_help_message(self):
        """Show the help message"""
        help_msg = "How may I assist you today?"
        self.add_jarvis_text(help_msg)

        # Also speak the time and help message if voice is available
        if hasattr(self, "voice_available") and self.voice_available:
            try:
                current_time = time.strftime("%H:%M")
                current_date = time.strftime("%A, %B %d, %Y")
                time_msg = f"The current time is {current_time}. Today is {current_date}."
                audio_data = self.tts.generate_audio(
                    time_msg + " " + help_msg, self.voice, self.speed
                )
                sd.play(audio_data, self.sample_rate)
            except Exception as e:
                print(f"Error playing welcome audio: {e}")

    def on_closing(self):
        """Handle window closing"""
        # Stop any active listening
        self.stop_listening()

        # Stop TTS thread
        if hasattr(self, "tts_thread_active"):
            self.tts_thread_active = False
            
        # Clear pending audio
        if hasattr(self, "pending_audio_chunks"):
            self.pending_audio_chunks.clear()

        # Shutdown executor if it exists
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)

        # Close the window
        self.root.destroy()

    def toggle_listening(self):
        """Toggle voice listening on/off"""
        if not hasattr(self, "voice_available") or not self.voice_available:
            self.add_text("Voice system is not available.", "error")
            return

        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def stop_listening(self):
        """Stop listening for voice input"""
        self.is_listening = False

        # Update UI
        if hasattr(self, "voice_button"):
            self.voice_button.update_theme(self.theme)
            # Update text directly
            self.voice_button.canvas.itemconfig(
                self.voice_button.button_text, text="START VOICE INPUT"
            )

        self.set_status("Online")


def run_jarvis_ui(fullscreen=True, dangerous=DEFAULT_DANGEROUS):
    """Run the JARVIS UI

    Args:
        fullscreen: Whether to run in fullscreen mode
        dangerous: Whether to use the dangerous/combat theme
    """
    # Create the Tkinter root window on the main thread
    root = tk.Tk()
    app = JarvisUI(root, fullscreen=fullscreen, dangerous=dangerous)

    # Set dark theme for ttk widgets
    style = ttk.Style()
    style.theme_use("clam")

    theme = get_theme("danger" if dangerous else "jarvis")

    style.configure(
        "TScrollbar",
        background=theme.background_color,
        troughcolor=theme.surface_color,
        bordercolor=theme.background_color,
        arrowcolor=theme.primary_color,
    )

    # Make window semi-transparent on supported platforms
    try:
        # Use different approach based on platform
        root.attributes("-alpha", 0.97)
    except:
        # If transparency is not supported, just continue without it
        print("Window transparency not supported on this platform")
        pass  # Not supported on this platform

    # Start the main loop on the main thread
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nShutting down JARVIS UI...")
    except Exception as e:
        print(f"Error in UI: {e}")

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple JARVIS UI Demo")
    parser.add_argument(
        "--windowed", action="store_true", help="Run in windowed mode instead of fullscreen"
    )
    parser.add_argument(
        "--combat", action="store_true", help="Run in combat mode instead of assistant mode"
    )

    args = parser.parse_args()

    print("Starting JARVIS UI Demo...")
    sys.exit(run_jarvis_ui(fullscreen=not args.windowed, dangerous=args.combat))
