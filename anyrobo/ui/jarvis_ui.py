import math
import queue
import random
import threading
import time
import tkinter as tk
from tkinter import font, ttk
from typing import Any, Dict, List, Optional

import numpy as np
import sounddevice as sd

from anyrobo.speech.recognition import SpeechRecognizer

# Import AnyRobo components
from anyrobo.speech.synthesis import TextToSpeech

# Dangerous color scheme
DANGER_RED = "#FF3030"
DANGER_ORANGE = "#FF7700"
WARNING_YELLOW = "#FFDD00"
ALERT_PINK = "#FF00FF"
NUCLEAR_GREEN = "#39FF14"
UI_BLUE = "#00FFFF"
UI_DARK_BLUE = "#001831"
BG_COLOR = "#000A14"


class CircularProgressAnimation:
    """Animated circular progress indicator for JARVIS UI"""

    def __init__(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        size: int = 100,
        color: str = "#5CE1E6",
        bg_color: str = "#002137",
        width: int = 8,
    ) -> None:
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.bg_color = bg_color
        self.width = width
        self.angle = 0
        self.arc_length = 120  # Degrees
        self.speed = 3
        self.running = False
        self.arc_id: Optional[int] = None
        self.bg_id: Optional[int] = None

        # Create background circle
        self.bg_id = self.canvas.create_oval(
            x - size / 2,
            y - size / 2,
            x + size / 2,
            y + size / 2,
            outline=bg_color,
            width=width,
            fill="",
        )

    def start(self) -> None:
        """Start the animation"""
        self.running = True
        self._animate()

    def _animate(self) -> None:
        """Animate the progress indicator"""
        if not self.running:
            return

        if self.arc_id:
            self.canvas.delete(self.arc_id)

        start_angle = self.angle
        # We don't need to calculate end_angle as we use arc_length directly in create_arc

        # Calculate arc coordinates
        x1 = self.x - self.size / 2
        y1 = self.y - self.size / 2
        x2 = self.x + self.size / 2
        y2 = self.y + self.size / 2

        self.arc_id = self.canvas.create_arc(
            x1,
            y1,
            x2,
            y2,
            start=start_angle,
            extent=self.arc_length,
            outline=self.color,
            width=self.width,
            style="arc",
        )

        self.angle = (self.angle + self.speed) % 360
        self.canvas.after(20, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False
        if self.arc_id:
            self.canvas.delete(self.arc_id)
            self.arc_id = None


class AudioVisualizer:
    """Audio visualizer for JARVIS UI"""

    def __init__(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        width: int = 200,
        height: int = 60,
        bars: int = 20,
        color: str = "#5CE1E6",
    ) -> None:
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bars = bars
        self.color = color
        self.bar_width = width / bars
        self.bar_ids: List[int] = []
        self.running = False

        # Create initial bars (all at minimum height)
        for i in range(bars):
            bar_x = x - width / 2 + i * self.bar_width
            bar_height = 2
            bar_id = canvas.create_rectangle(
                bar_x,
                y - bar_height / 2,
                bar_x + self.bar_width - 1,
                y + bar_height / 2,
                fill=color,
                outline="",
            )
            self.bar_ids.append(bar_id)

    def start(self) -> None:
        """Start the visualizer animation"""
        self.running = True
        self._animate()

    def _animate(self) -> None:
        """Animate the audio visualizer"""
        if not self.running:
            return

        # Generate random heights for demo
        heights = [random.randint(2, self.height) for _ in range(self.bars)]

        # Update bar heights
        for i, bar_id in enumerate(self.bar_ids):
            bar_x = self.x - self.width / 2 + i * self.bar_width
            bar_height = heights[i]
            self.canvas.coords(
                bar_id,
                bar_x,
                self.y - bar_height / 2,
                bar_x + self.bar_width - 1,
                self.y + bar_height / 2,
            )

        self.canvas.after(100, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False
        # Reset to minimum height
        for i, bar_id in enumerate(self.bar_ids):
            bar_x = self.x - self.width / 2 + i * self.bar_width
            bar_height = 2
            self.canvas.coords(
                bar_id,
                bar_x,
                self.y - bar_height / 2,
                bar_x + self.bar_width - 1,
                self.y + bar_height / 2,
            )


class PulsatingCircle:
    """Pulsating circle animation for JARVIS UI"""

    def __init__(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        min_radius: float = 20,
        max_radius: float = 30,
        color: str = "#5CE1E6",
        pulse_speed: float = 0.05,
    ) -> None:
        self.canvas = canvas
        self.x = x
        self.y = y
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.current_radius = min_radius
        self.color = color
        self.pulse_speed = pulse_speed
        self.growing = True
        self.circle_id: Optional[int] = None
        self.running = False

        # Create initial circle
        self.circle_id = canvas.create_oval(
            x - min_radius, y - min_radius, x + min_radius, y + min_radius, fill=color, outline=""
        )

    def start(self) -> None:
        """Start the pulsating animation"""
        self.running = True
        self._animate()

    def _animate(self) -> None:
        """Animate the pulsating circle"""
        if not self.running:
            return

        if self.growing:
            self.current_radius += self.pulse_speed
            if self.current_radius >= self.max_radius:
                self.growing = False
        else:
            self.current_radius -= self.pulse_speed
            if self.current_radius <= self.min_radius:
                self.growing = True

        if self.circle_id is not None:
            self.canvas.coords(
                self.circle_id,
                int(self.x - self.current_radius),
                int(self.y - self.current_radius),
                int(self.x + self.current_radius),
                int(self.y + self.current_radius),
            )

        self.canvas.after(20, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False
        # Reset to minimum radius
        if self.circle_id is not None:
            self.canvas.coords(
                self.circle_id,
                int(self.x - self.min_radius),
                int(self.y - self.min_radius),
                int(self.x + self.min_radius),
                int(self.y + self.min_radius),
            )


class HexagonGrid:
    """Animated hexagonal grid for UI backgrounds.

    This component creates a grid of hexagons that can pulse or change visibility
    for a futuristic background effect.

    Args:
        canvas: The tkinter canvas to draw on
        size: Size of each hexagon
        gap: Gap between hexagons
        color: Color of the hexagons
        alpha: Transparency of the hexagons (not fully supported in Tkinter)
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        size: int = 40,
        gap: int = 10,
        color: str = UI_BLUE,
        alpha: float = 0.2,
    ) -> None:
        self.canvas = canvas
        self.size = size
        self.gap = gap
        self.color = color
        self.alpha = alpha
        self.hexagons: List[Dict[str, Any]] = []
        self.running = False
        self.create_grid()

    def create_grid(self) -> None:
        """Create hexagonal grid to cover the canvas"""
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 600

        # Calculate hex dimensions
        hex_width = self.size * 2
        hex_height = self.size * math.sqrt(3)

        # Calculate number of hexagons needed
        cols = int(width / (hex_width * 0.75 + self.gap)) + 2
        rows = int(height / (hex_height + self.gap)) + 2

        # Create hexagons
        for row in range(rows):
            for col in range(cols):
                # Calculate position with offset for even rows
                x = col * (hex_width * 0.75 + self.gap)
                y = row * (hex_height + self.gap)
                if col % 2 == 1:
                    y += hex_height / 2

                # Create hexagon points
                points = []
                for i in range(6):
                    angle = math.radians(60 * i + 30)
                    px = x + self.size * math.cos(angle)
                    py = y + self.size * math.sin(angle)
                    points.extend([px, py])

                # Random alpha for each hexagon
                alpha = random.uniform(0.1, 0.3)
                hex_color = self.color + f"{int(alpha * 255):02x}"

                # Draw hexagon
                hex_id = self.canvas.create_polygon(points, fill="", outline=hex_color, width=1)

                # Store hexagon info
                self.hexagons.append(
                    {
                        "id": hex_id,
                        "points": points,
                        "pulse": random.random(),
                        "pulse_speed": random.uniform(0.01, 0.05),
                        "color": hex_color,
                    }
                )

    def start(self) -> None:
        """Start the animation"""
        self.running = True
        self._animate()

    def _animate(self) -> None:
        """Animate the hexagonal grid"""
        if not self.running:
            return

        for hex_data in self.hexagons:
            # Update pulse value
            hex_data["pulse"] = (hex_data["pulse"] + hex_data["pulse_speed"]) % 1.0

            # Toggle visibility occasionally
            if random.random() < 0.05:  # 5% chance to toggle visibility
                current_state = self.canvas.itemcget(hex_data["id"], "state")
                new_state = "hidden" if current_state == "normal" else "normal"
                self.canvas.itemconfig(hex_data["id"], state=new_state)

        self.canvas.after(50, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False


class ScanLine:
    """Animated scan line effect for JARVIS UI"""

    def __init__(
        self, canvas: tk.Canvas, color: str = UI_BLUE, speed: int = 2, thickness: int = 3
    ) -> None:
        self.canvas = canvas
        self.color = color
        self.speed = speed
        self.thickness = thickness
        self.position = 0
        self.scan_id: Optional[int] = None
        self.running = False

    def start(self) -> None:
        """Start the scan line animation"""
        self.running = True
        self._animate()

    def _animate(self) -> None:
        """Animate the scan line"""
        if not self.running:
            return

        height = self.canvas.winfo_height() or 600
        width = self.canvas.winfo_width() or 800

        # Delete previous line
        if self.scan_id:
            self.canvas.delete(self.scan_id)

        # Create new scan line
        self.scan_id = self.canvas.create_line(
            0,
            self.position,
            width,
            self.position,
            fill=self.color,
            width=self.thickness,
            dash=(10, 5),
        )

        # Update position
        self.position = (self.position + self.speed) % height

        self.canvas.after(20, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False
        if self.scan_id:
            self.canvas.delete(self.scan_id)
            self.scan_id = None


class TargetLock:
    """Animated target lock/crosshair effect"""

    def __init__(
        self, canvas: tk.Canvas, x: int, y: int, size: int = 50, color: str = DANGER_RED
    ) -> None:
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.shapes: List[int] = []
        self.rotation = 0
        self.running = False

    def _create_shapes(self) -> None:
        """Create target lock shapes"""
        # Delete previous shapes
        for shape_id in self.shapes:
            self.canvas.delete(shape_id)
        self.shapes = []

        # Create outer circle
        id1 = self.canvas.create_oval(
            self.x - self.size,
            self.y - self.size,
            self.x + self.size,
            self.y + self.size,
            outline=self.color,
            width=2,
            dash=(5, 3),
        )
        self.shapes.append(id1)

        # Create inner circle
        id2 = self.canvas.create_oval(
            self.x - self.size / 2,
            self.y - self.size / 2,
            self.x + self.size / 2,
            self.y + self.size / 2,
            outline=self.color,
            width=1,
        )
        self.shapes.append(id2)

        # Create crosshairs (rotated)
        rad = math.radians(self.rotation)
        sin_r = math.sin(rad)
        cos_r = math.cos(rad)

        # Horizontal line
        line_length = self.size * 1.5
        x1 = self.x - line_length * cos_r
        y1 = self.y - line_length * sin_r
        x2 = self.x + line_length * cos_r
        y2 = self.y + line_length * sin_r

        id3 = self.canvas.create_line(x1, y1, x2, y2, fill=self.color, width=1)
        self.shapes.append(id3)

        # Vertical line (perpendicular to the first)
        x1 = self.x + line_length * sin_r
        y1 = self.y - line_length * cos_r
        x2 = self.x - line_length * sin_r
        y2 = self.y + line_length * cos_r

        id4 = self.canvas.create_line(x1, y1, x2, y2, fill=self.color, width=1)
        self.shapes.append(id4)

    def start(self) -> None:
        """Start the target lock animation"""
        self.running = True
        self._animate()

    def _animate(self) -> None:
        """Animate the target lock"""
        if not self.running:
            return

        # Update rotation
        self.rotation = (self.rotation + 1) % 360

        # Recreate shapes with new rotation
        self._create_shapes()

        self.canvas.after(30, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False
        # Delete shapes
        for shape_id in self.shapes:
            self.canvas.delete(shape_id)
        self.shapes = []

    def set_position(self, x: int, y: int) -> None:
        """Update the position of the target lock"""
        self.x = x
        self.y = y


class LiveAudioVisualizer(AudioVisualizer):
    """Enhanced audio visualizer that can use real audio data"""

    def __init__(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        width: int = 200,
        height: int = 60,
        bars: int = 20,
        color: str = UI_BLUE,
    ) -> None:
        super().__init__(canvas, x, y, width, height, bars, color)
        self.audio_data: Optional[np.ndarray] = None
        self.is_live = False

    def set_audio_data(self, audio_data: np.ndarray) -> None:
        """Set audio data for visualization"""
        self.audio_data = audio_data
        self.is_live = True

    def _animate(self) -> None:
        """Animate the audio visualizer"""
        if not self.running:
            return

        if self.is_live and self.audio_data is not None:
            # Use real audio data
            audio_len = len(self.audio_data)
            if audio_len > 0:
                # Calculate energy levels for each bar
                chunk_size = audio_len // self.bars
                heights = []

                for i in range(self.bars):
                    start = i * chunk_size
                    end = min(start + chunk_size, audio_len)
                    if start < end:
                        # Calculate energy/amplitude for this chunk
                        chunk = self.audio_data[start:end]
                        energy = np.sqrt(np.mean(chunk**2)) * self.height * 10
                        # Cap the height
                        bar_height = min(max(2, energy), self.height)
                        heights.append(bar_height)
                    else:
                        heights.append(2)  # Minimum height

                # Update bar heights
                for i, bar_id in enumerate(self.bar_ids):
                    if i < len(heights):
                        bar_x = self.x - self.width / 2 + i * self.bar_width
                        bar_height = heights[i]
                        self.canvas.coords(
                            bar_id,
                            bar_x,
                            self.y - bar_height / 2,
                            bar_x + self.bar_width - 1,
                            self.y + bar_height / 2,
                        )
            else:
                # Use random heights as fallback
                heights = [random.randint(2, self.height) for _ in range(self.bars)]

                # Update bar heights
                for i, bar_id in enumerate(self.bar_ids):
                    bar_x = self.x - self.width / 2 + i * self.bar_width
                    bar_height = heights[i]
                    self.canvas.coords(
                        bar_id,
                        bar_x,
                        self.y - bar_height / 2,
                        bar_x + self.bar_width - 1,
                        self.y + bar_height / 2,
                    )
        else:
            # Use random heights for demo
            super()._animate()
            return

        self.canvas.after(50, self._animate)


class JarvisUI:
    """JARVIS-inspired UI with animations, text display, and voice status"""

    def __init__(self, root: tk.Tk, fullscreen: bool = True, dangerous: bool = True) -> None:
        self.root = root
        self.root.title("J.A.R.V.I.S - ADVANCED COMBAT INTERFACE")
        self.root.configure(bg=BG_COLOR)

        # Fullscreen mode
        self.fullscreen = fullscreen
        if fullscreen:
            self.root.attributes("-fullscreen", True)
            # Bind Escape key to exit fullscreen
            self.root.bind("<Escape>", self.toggle_fullscreen)
        else:
            # Set minimum window size
            self.root.minsize(1024, 768)

        # Choose color scheme based on dangerous mode
        self.dangerous = dangerous
        self.primary_color = DANGER_RED if dangerous else UI_BLUE
        self.secondary_color = DANGER_ORANGE if dangerous else "#007ACC"
        self.accent_color = WARNING_YELLOW if dangerous else "#00AAFF"

        # Configure fonts
        self.setup_fonts()

        # Initialize speech components
        self.setup_speech()

        # Create main frame
        self.main_frame = tk.Frame(root, bg=BG_COLOR)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create header with title
        self.create_header()

        # Create canvas for animations
        self.create_animation_canvas()

        # Create text display area
        self.create_text_display()

        # Create voice control panel
        self.create_voice_controls()

        # Create status bar
        self.create_status_bar()

        # Start animations
        self.start_animations()

        # Bind resize event
        self.root.bind("<Configure>", self.on_resize)

        # Audio processing
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self.recording = False
        self.is_listening = False

        # Initialize TTS and STT as Optional
        self.tts: Optional[TextToSpeech] = None
        self.stt: Optional[SpeechRecognizer] = None

    def setup_fonts(self) -> None:
        """Setup custom fonts for the UI"""
        self.title_font = font.Font(family="Helvetica", size=28, weight="bold")
        self.text_font = font.Font(family="Courier", size=14)
        self.status_font = font.Font(family="Helvetica", size=11)
        self.button_font = font.Font(family="Helvetica", size=12, weight="bold")

    def setup_speech(self) -> None:
        """Setup speech recognition and synthesis"""
        try:
            self.tts = TextToSpeech()
            self.voice = "en_us_006"  # Default voice
            self.speech_speed = 1.0

            # Initialize speech recognizer
            self.stt = SpeechRecognizer()
        except Exception as e:
            print(f"Error setting up speech components: {e}")
            self.tts = None
            self.stt = None

    def toggle_fullscreen(self, event: Optional[tk.Event] = None) -> str:
        """Toggle fullscreen mode"""
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        return "break"

    def create_header(self) -> None:
        """Create the header section with title"""
        header_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        # Create an alert banner
        alert_frame = tk.Frame(header_frame, bg=self.primary_color, height=30)
        alert_frame.pack(fill=tk.X, pady=(0, 10))

        alert_text = "SECURITY LEVEL: MAXIMUM" if self.dangerous else "SYSTEM STATUS: ONLINE"
        alert_label = tk.Label(
            alert_frame, text=alert_text, font=self.status_font, fg="white", bg=self.primary_color
        )
        alert_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Blinking classified indicator if dangerous
        if self.dangerous:
            self.classified_label = tk.Label(
                alert_frame,
                text="⚠ CLASSIFIED ⚠",
                font=self.status_font,
                fg="black",
                bg=WARNING_YELLOW,
            )
            self.classified_label.pack(side=tk.RIGHT, padx=10, pady=5)
            # Start blinking
            self.blink_classified()

        # Main title
        title_text = "J.A.R.V.I.S COMBAT INTERFACE" if self.dangerous else "J.A.R.V.I.S"
        title_label = tk.Label(
            header_frame, text=title_text, font=self.title_font, fg=self.primary_color, bg=BG_COLOR
        )
        title_label.pack(side=tk.LEFT)

        subtitle_text = "JUST A RATHER VERY INTELLIGENT SYSTEM"
        subtitle_label = tk.Label(
            header_frame, text=subtitle_text, font=self.status_font, fg="#AAAAAA", bg=BG_COLOR
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=(8, 0))

    def blink_classified(self) -> None:
        """Blink the classified indicator"""
        if not hasattr(self, "classified_label"):
            return

        current_bg = self.classified_label.cget("background")
        new_bg = WARNING_YELLOW if current_bg == self.primary_color else self.primary_color
        self.classified_label.config(background=new_bg)
        self.root.after(500, self.blink_classified)

    def create_animation_canvas(self) -> None:
        """Create canvas for animations"""
        canvas_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Create animations
        self.setup_animations()

    def setup_animations(self) -> None:
        """Setup all animations on the canvas"""
        canvas_width = self.canvas.winfo_width() or 1024
        canvas_height = self.canvas.winfo_height() or 500

        # Create hexagonal grid background
        self.hex_grid = HexagonGrid(self.canvas, size=30, color=self.primary_color)

        # Create scan line
        self.scan_line = ScanLine(self.canvas, color=self.accent_color)

        # Circular progress animation (top-left)
        self.circle_progress = CircularProgressAnimation(
            self.canvas,
            int(canvas_width * 0.15),
            int(canvas_height * 0.25),
            size=80,
            color=self.primary_color,
            bg_color=BG_COLOR,
        )

        # Audio visualizer (bottom)
        self.audio_vis = LiveAudioVisualizer(
            self.canvas,
            int(canvas_width * 0.5),
            int(canvas_height * 0.85),
            width=int(canvas_width * 0.7),
            height=50,
            bars=40,
            color=self.primary_color,
        )

        # Pulsating circle (top-right)
        self.pulse_circle = PulsatingCircle(
            self.canvas,
            int(canvas_width * 0.85),
            int(canvas_height * 0.25),
            min_radius=20,
            max_radius=30,
            color=self.primary_color,
        )

        # Target lock (center)
        if self.dangerous:
            self.target_lock = TargetLock(
                self.canvas,
                int(canvas_width * 0.5),
                int(canvas_height * 0.4),
                size=70,
                color=DANGER_RED,
            )

        # Add text and decorative elements
        status_text = "WEAPONS ONLINE" if self.dangerous else "SYSTEMS ONLINE"
        self.status_text = self.canvas.create_text(
            canvas_width * 0.5,
            canvas_height * 0.5,
            text=status_text,
            fill=self.primary_color,
            font=self.title_font,
        )

        # Add timestamp and coordinates for military feel
        coords_text = "LAT: 37.7749° N | LON: 122.4194° W | ALT: 52m"
        self.coords_text = self.canvas.create_text(
            canvas_width * 0.85,
            canvas_height * 0.95,
            text=coords_text,
            fill=self.secondary_color,
            font=self.status_font,
            anchor="se",
        )

    def start_animations(self) -> None:
        """Start all animations"""
        self.hex_grid.start()
        self.scan_line.start()
        self.circle_progress.start()
        self.audio_vis.start()
        self.pulse_circle.start()
        if self.dangerous and hasattr(self, "target_lock"):
            self.target_lock.start()

    def stop_animations(self) -> None:
        """Stop all animations"""
        self.hex_grid.stop()
        self.scan_line.stop()
        self.circle_progress.stop()
        self.audio_vis.stop()
        self.pulse_circle.stop()
        if self.dangerous and hasattr(self, "target_lock"):
            self.target_lock.stop()

    def create_text_display(self) -> None:
        """Create the text display area"""
        text_frame = tk.Frame(self.main_frame, bg=UI_DARK_BLUE, padx=10, pady=10)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # Make text frame have a colored border
        text_frame.config(highlightbackground=self.primary_color, highlightthickness=2)

        self.text_display = tk.Text(
            text_frame,
            bg=UI_DARK_BLUE,
            fg="#FFFFFF",
            font=self.text_font,
            wrap=tk.WORD,
            height=10,
            bd=0,
            padx=5,
            pady=5,
            insertbackground=self.primary_color,  # Cursor color
        )
        self.text_display.pack(fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.text_display, command=self.text_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_display.config(yscrollcommand=scrollbar.set)

        # Configure tag for JARVIS text
        self.text_display.tag_configure("jarvis", foreground=self.primary_color)
        self.text_display.tag_configure("user", foreground="#FFFFFF")
        self.text_display.tag_configure("warning", foreground=WARNING_YELLOW)
        self.text_display.tag_configure("error", foreground=DANGER_RED)

        # Add some initial text
        self.add_jarvis_text("JARVIS combat interface initialized. Awaiting instructions.")
        if self.dangerous:
            self.add_text("WARNING: Combat mode activated. Weapon systems online.", "warning")

    def create_voice_controls(self) -> None:
        """Create voice control buttons"""
        control_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # Voice button
        self.voice_button = tk.Button(
            control_frame,
            text="START VOICE COMMAND",
            font=self.button_font,
            bg=self.primary_color,
            fg="white",
            activebackground=self.secondary_color,
            activeforeground="white",
            bd=0,
            padx=15,
            pady=8,
            command=self.toggle_voice_recording,
        )
        self.voice_button.pack(side=tk.LEFT, padx=(0, 10))

        # Voice status indicator
        self.voice_status = tk.Label(
            control_frame,
            text="Voice Recognition: IDLE",
            font=self.status_font,
            fg="#AAAAAA",
            bg=BG_COLOR,
        )
        self.voice_status.pack(side=tk.LEFT, padx=10, pady=8)

    def toggle_voice_recording(self) -> None:
        """Toggle voice recording on/off"""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self) -> None:
        """Start recording audio for voice recognition"""
        if self.recording:
            return

        self.recording = True
        self.voice_button.config(text="STOP VOICE COMMAND", bg=DANGER_RED)
        self.voice_status.config(text="Voice Recognition: LISTENING", fg=self.primary_color)
        self.set_status("Listening")

        # Start recording in a separate thread
        threading.Thread(target=self._record_audio, daemon=True).start()

    def stop_recording(self) -> None:
        """Stop recording audio"""
        self.recording = False
        self.voice_button.config(text="START VOICE COMMAND", bg=self.primary_color)
        self.voice_status.config(text="Voice Recognition: IDLE", fg="#AAAAAA")
        self.set_status("Online")

    def _record_audio(self) -> None:
        """Record audio and process it"""
        try:
            # Sample rate and channels
            sample_rate = 16000
            channels = 1
            chunk_size = 1024

            # Start audio stream
            self.audio_data = np.array([], dtype=np.float32)

            def callback(indata: np.ndarray, frames: int, time: Any, status: Any) -> None:
                """Callback for audio stream"""
                # Append data to the queue
                self.audio_queue.put(indata.copy())

                # Update audio visualizer
                if hasattr(self, "audio_vis"):
                    # Normalize and scale for visualization
                    scaled_data = indata.flatten() * 5
                    self.audio_vis.set_audio_data(scaled_data)

            # Start the stream
            with sd.InputStream(
                samplerate=sample_rate, channels=channels, callback=callback, blocksize=chunk_size
            ):
                self.add_user_text("(Listening...)")

                # Wait for recording to stop or timeout
                start_time = time.time()
                max_duration = 15  # Maximum recording duration in seconds

                while self.recording and (time.time() - start_time) < max_duration:
                    # Get data from queue
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        # Append to audio data
                        self.audio_data = np.append(self.audio_data, data.flatten())
                    except queue.Empty:
                        continue

                # Process the recorded audio
                if len(self.audio_data) > 0:
                    self.voice_status.config(
                        text="Voice Recognition: PROCESSING", fg=WARNING_YELLOW
                    )
                    self.set_status("Processing")

                    # Use anyrobo's speech recognition
                    if self.stt:
                        try:
                            result = self.stt.transcribe(self.audio_data)
                            text = result.get("text", "").strip()

                            if text:
                                # Update UI with recognized text
                                self.add_user_text(text)

                                # Process command (can be customized)
                                self.process_voice_command(text)
                            else:
                                self.add_text("No speech detected.", "error")
                        except Exception as e:
                            self.add_text(f"Speech recognition error: {str(e)}", "error")
                    else:
                        self.add_text("Speech recognition not available.", "error")

                # Reset audio visualizer
                if hasattr(self, "audio_vis"):
                    self.audio_vis.is_live = False

        except Exception as e:
            self.add_text(f"Audio recording error: {str(e)}", "error")
        finally:
            self.stop_recording()

    def process_voice_command(self, text: str) -> None:
        """Process a voice command"""
        text_lower = text.lower()

        # Simple command processing
        if "hello" in text_lower or "hi jarvis" in text_lower:
            response = "Hello. I am at your service."
        elif "status" in text_lower:
            response = "All systems are functioning at optimal levels."
        elif "time" in text_lower:
            current_time = time.strftime("%H:%M:%S")
            response = f"The current time is {current_time}."
        elif "date" in text_lower:
            current_date = time.strftime("%A, %B %d, %Y")
            response = f"Today is {current_date}."
        elif "weapon" in text_lower or "combat" in text_lower:
            if self.dangerous:
                response = "Weapon systems are online and ready. Please specify target parameters."
            else:
                response = "Combat systems are currently in standby mode. Authorization required."
        elif "exit" in text_lower or "quit" in text_lower or "close" in text_lower:
            response = "Shutting down interface."
            self.add_jarvis_text(response)
            self.speak(response)
            self.root.after(2000, self.root.quit)
            return
        elif "fullscreen" in text_lower:
            self.toggle_fullscreen()
            response = "Toggling fullscreen mode."
        else:
            response = "I'm sorry, I don't understand that command."

        # Display and speak response
        self.add_jarvis_text(response)
        self.speak(response)

    def speak(self, text: str) -> None:
        """Convert text to speech using TTS"""
        if not text or not self.tts:
            return

        try:
            # Generate audio
            audio_data = self.tts.generate_audio(text, self.voice, self.speech_speed)

            # Play audio in a separate thread
            def play_audio() -> None:
                try:
                    # Play the audio
                    sd.play(audio_data, 24000)
                    sd.wait()
                except Exception as e:
                    print(f"Error playing audio: {e}")

            threading.Thread(target=play_audio, daemon=True).start()

        except Exception as e:
            print(f"Speech synthesis error: {e}")

    def create_status_bar(self) -> None:
        """Create the status bar at the bottom"""
        status_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        # Left status indicator
        self.status_left = tk.Label(
            status_frame,
            text="Status: Online",
            font=self.status_font,
            fg=self.primary_color,
            bg=BG_COLOR,
        )
        self.status_left.pack(side=tk.LEFT)

        # Center indicator for warnings
        self.status_center = tk.Label(
            status_frame, text="", font=self.status_font, fg=WARNING_YELLOW, bg=BG_COLOR
        )
        self.status_center.pack(side=tk.LEFT, padx=20)

        # Right status with time
        self.status_right = tk.Label(
            status_frame, text="", font=self.status_font, fg="#AAAAAA", bg=BG_COLOR
        )
        self.status_right.pack(side=tk.RIGHT)

        # Update clock
        self.update_clock()

    def update_clock(self) -> None:
        """Update the clock in the status bar"""
        current_time = time.strftime("%H:%M:%S")
        self.status_right.config(text=f"System Time: {current_time}")

        # Update timestamp on canvas if it exists
        if hasattr(self, "coords_text") and self.canvas.winfo_exists():
            coords_text = f"LAT: 37.7749° N | LON: 122.4194° W | ALT: 52m | {current_time}"
            self.canvas.itemconfig(self.coords_text, text=coords_text)

        self.root.after(1000, self.update_clock)

    def add_jarvis_text(self, text: str) -> None:
        """Add text from JARVIS to the display"""
        self.text_display.config(state=tk.NORMAL)
        self.text_display.insert(tk.END, "JARVIS: ", "jarvis")
        self.text_display.insert(tk.END, f"{text}\n\n")
        self.text_display.see(tk.END)
        self.text_display.config(state=tk.DISABLED)

    def add_user_text(self, text: str) -> None:
        """Add user text to the display"""
        self.text_display.config(state=tk.NORMAL)
        self.text_display.insert(tk.END, "User: ", "user")
        self.text_display.insert(tk.END, f"{text}\n\n")
        self.text_display.see(tk.END)
        self.text_display.config(state=tk.DISABLED)

    def add_text(self, text: str, tag: Optional[str] = None) -> None:
        """Add text with optional formatting"""
        self.text_display.config(state=tk.NORMAL)
        if tag:
            self.text_display.insert(tk.END, f"{text}\n\n", tag)
        else:
            self.text_display.insert(tk.END, f"{text}\n\n")
        self.text_display.see(tk.END)
        self.text_display.config(state=tk.DISABLED)

    def set_status(self, text: str) -> None:
        """Update the status text"""
        self.status_left.config(text=f"Status: {text}")

    def set_warning(self, text: str) -> None:
        """Set warning text in status bar"""
        self.status_center.config(text=text)

    def on_resize(self, event: Any) -> None:
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


def run_jarvis_ui(fullscreen: bool = True, dangerous: bool = True) -> None:
    """Run the JARVIS UI

    Args:
        fullscreen: Whether to run in fullscreen mode
        dangerous: Whether to use the dangerous/combat theme
    """
    root = tk.Tk()
    app = JarvisUI(root, fullscreen=fullscreen, dangerous=dangerous)

    # Set dark theme for ttk widgets
    style = ttk.Style()
    style.theme_use("clam")

    primary_color = DANGER_RED if dangerous else UI_BLUE

    style.configure(
        "TScrollbar",
        background=BG_COLOR,
        troughcolor=UI_DARK_BLUE,
        bordercolor=BG_COLOR,
        arrowcolor=primary_color,
    )

    # Make window semi-transparent on supported platforms
    try:
        root.attributes("-alpha", 0.97)
    except Exception:  # Fixed bare except
        pass  # Not supported on this platform

    # Example of adding text after a delay
    def delayed_text() -> None:
        time.sleep(2)
        app.add_jarvis_text("All systems are functioning at optimal levels.")

        # If TTS is available, speak the text
        if hasattr(app, "tts") and app.tts:
            app.speak("All systems are functioning at optimal levels.")

        time.sleep(2)

        if dangerous:
            app.set_warning("COMBAT PROTOCOLS ACTIVE")
            time.sleep(1)
            app.add_text("WARNING: Unauthorized access detected in sector 7-G", "warning")
            time.sleep(1.5)
            app.add_jarvis_text("Security breach contained. Defensive protocols engaged.")
            if hasattr(app, "tts") and app.tts:
                app.speak("Security breach contained. Defensive protocols engaged.")

    # Start the delayed text in a separate thread
    threading.Thread(target=delayed_text, daemon=True).start()

    root.mainloop()


if __name__ == "__main__":
    run_jarvis_ui(fullscreen=True, dangerous=True)
