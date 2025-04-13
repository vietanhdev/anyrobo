"""Audio visualization components for the anyrobo UI system."""

import random
import tkinter as tk
from typing import List, Optional, Union

import numpy as np

from anyrobo.ui.themes import UITheme, get_theme

# UI colors
UI_BLUE = "#00FFFF"


class AudioVisualizer:
    """Audio visualizer for UI interfaces.

    This component creates a bar-based audio visualizer that can animate
    to represent audio input or output.

    Args:
        canvas: The tkinter canvas to draw on
        x: X-coordinate of the center of the visualizer
        y: Y-coordinate of the center of the visualizer
        width: Width of the entire visualizer
        height: Maximum height of the bars
        bars: Number of bars to display
        color: Color of the bars
    """

    def __init__(
        self,
        canvas: "tk.Canvas",
        x: int,
        y: int,
        width: int = 200,
        height: int = 60,
        bars: int = 20,
        color: str = UI_BLUE,
    ) -> None:
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bars = bars
        self.color = color
        self.bar_width = width / bars
        self.bar_ids = []
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

    def set_heights(self, heights: List[float]) -> None:
        """Set the heights of the bars directly

        Args:
            heights: List of height values for each bar
        """
        if len(heights) != len(self.bar_ids):
            # Resize to match if necessary
            heights = (
                heights[: len(self.bar_ids)]
                if len(heights) > len(self.bar_ids)
                else heights + [2] * (len(self.bar_ids) - len(heights))
            )

        for i, bar_id in enumerate(self.bar_ids):
            bar_x = self.x - self.width / 2 + i * self.bar_width
            bar_height = min(max(2, heights[i]), self.height)  # Clamp between 2 and max height
            self.canvas.coords(
                bar_id,
                bar_x,
                self.y - bar_height / 2,
                bar_x + self.bar_width - 1,
                self.y + bar_height / 2,
            )


class LiveAudioVisualizer(AudioVisualizer):
    """Live audio visualizer that can display real-time audio data.

    This extends the base AudioVisualizer to work with real-time
    audio data from a microphone or audio stream.

    Args:
        canvas: The tkinter canvas to draw on
        x: X-coordinate of the center of the visualizer
        y: Y-coordinate of the center of the visualizer
        width: Width of the entire visualizer
        height: Maximum height of the bars
        bars: Number of bars to display
        color: Color of the bars
    """

    def __init__(
        self,
        canvas: Union["tk.Canvas", tk.Widget],
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: int = 200,
        height: int = 60,
        bars: int = 20,
        color: str = UI_BLUE,
        theme: Optional[Union[UITheme, str]] = None,
    ) -> None:
        # If canvas is not a Canvas but a widget, create a Canvas
        if not isinstance(canvas, tk.Canvas):
            # Get background color from theme
            bg_color = "black"
            if theme is not None:
                if isinstance(theme, str):
                    theme_obj = get_theme(theme)
                    bg_color = theme_obj.background_color
                else:
                    theme_obj = theme
                    bg_color = theme_obj.background_color

            # Create frame with proper background
            frame = tk.Frame(canvas, bg=bg_color)
            frame.pack(pady=10, fill=tk.X)
            canvas = tk.Canvas(frame, width=width, height=height, bg=bg_color, highlightthickness=0)
            canvas.pack()

        # If theme is provided, use its colors
        theme_obj = None
        if theme is not None:
            if isinstance(theme, str):
                theme_obj = get_theme(theme)
            else:
                theme_obj = theme

            # Update color from theme
            color = theme_obj.accent_color

        # If x and y are not provided, center in the canvas
        if x is None:
            x = width // 2
        if y is None:
            y = height // 2

        super().__init__(canvas, x, y, width, height, bars, color)
        self.audio_data = None
        self.energy_scale = 5.0  # Fixed scale factor as a float

    def set_audio_data(self, audio_data: np.ndarray) -> None:
        """Set the current audio data to visualize

        Args:
            audio_data: NumPy array of audio samples
        """
        self.audio_data = audio_data

    def _animate(self) -> None:
        """Animate the audio visualizer based on actual audio data"""
        if not self.running:
            return

        if self.audio_data is not None and len(self.audio_data) > 0:
            # Process audio data into bar heights
            chunk_size = len(self.audio_data) // self.bars
            if chunk_size > 0:
                heights = []
                for i in range(self.bars):
                    start = i * chunk_size
                    end = min(start + chunk_size, len(self.audio_data))
                    if start < end:
                        # Calculate energy for this chunk
                        chunk = self.audio_data[start:end]
                        # Use RMS (root mean square) energy
                        # Make sure we're using numeric values for calculation
                        energy = (
                            float(np.sqrt(np.mean(chunk**2))) * float(self.height) * 5.0
                        )  # Use fixed scale factor
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
                # Fall back to random animation if no audio data
                heights = [random.randint(2, int(self.height * 0.2)) for _ in range(self.bars)]
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
            # Fall back to random animation if no audio data
            heights = [random.randint(2, int(self.height * 0.2)) for _ in range(self.bars)]
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

        self.canvas.after(50, self._animate)  # Smoother animation

    def process_audio_frame(self, audio_frame: np.ndarray) -> float:
        """Process an audio frame and return its energy level

        Args:
            audio_frame: Audio frame data

        Returns:
            Energy level of the frame
        """
        return np.sqrt(np.mean(audio_frame**2)) * self.height * self.energy_scale
