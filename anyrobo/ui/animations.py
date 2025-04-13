"""Animation components for the anyrobo UI system."""

import math
import random
import tkinter as tk
from dataclasses import dataclass
from typing import List, Optional, Union

from anyrobo.ui.themes import UITheme, get_theme

# UI colors
UI_BLUE = "#00FFFF"
UI_DARK_BLUE = "#001831"
BG_COLOR = "#000A14"
DANGER_RED = "#FF3030"
WARNING_YELLOW = "#FFDD00"


@dataclass
class HexagonData:
    """Data for a single hexagon in the grid."""

    id: int
    points: List[float]
    pulse: float
    pulse_speed: float
    brightness: float


class CircularProgressAnimation:
    """Circular progress animation for UI interfaces.

    This component creates a circular arc that rotates to indicate
    progress or an ongoing operation.

    Args:
        canvas: The tkinter canvas or widget to draw on
        x: X-coordinate of the center of the animation
        y: Y-coordinate of the center of the animation
        size: Diameter of the circle
        color: Color of the progress arc
        bg_color: Background circle color
        width: Line width of the circle
        theme: Optional UITheme instance or theme name
    """

    def __init__(
        self,
        canvas: Union[tk.Canvas, tk.Widget],
        x: int = None,
        y: int = None,
        size: int = 100,
        color: str = "#5CE1E6",
        bg_color: str = "#002137",
        width: int = 8,
        theme: Optional[Union[UITheme, str]] = None,
    ) -> None:
        # If canvas is not a Canvas but a widget, create a Canvas
        if not isinstance(canvas, tk.Canvas):
            frame = tk.Frame(canvas, bg="black")
            frame.pack(pady=10, fill=tk.X)
            self.canvas = tk.Canvas(frame, width=400, height=400, bg="black", highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas = canvas

        # Handle canvas size for positioning
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600

        # Default center position if not specified
        if x is None:
            x = canvas_width // 2
        if y is None:
            y = canvas_height // 2

        self.x = x
        self.y = y
        self.size = size

        # Handle theme if provided
        if theme is not None:
            if isinstance(theme, str):
                theme_obj = get_theme(theme)
            else:
                theme_obj = theme
            self.color = theme_obj.accent_color
            self.bg_color = theme_obj.surface_color
        else:
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
            outline=self.bg_color,
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


class PulsatingCircle:
    """Pulsating circle animation for UI interfaces.

    This component creates a circle that pulses between a minimum and maximum size.

    Args:
        canvas: The tkinter canvas or widget to draw on
        x: X-coordinate of the center of the circle
        y: Y-coordinate of the center of the circle
        min_radius: Minimum radius of the circle
        max_radius: Maximum radius of the circle
        color: Color of the circle
        pulse_speed: Speed of the pulsating effect
        theme: Optional UITheme instance or theme name
    """

    def __init__(
        self,
        canvas: Union[tk.Canvas, tk.Widget],
        x: int = None,
        y: int = None,
        min_radius: float = 20,
        max_radius: float = 30,
        color: str = "#5CE1E6",
        pulse_speed: float = 0.05,
        theme: Optional[Union[UITheme, str]] = None,
    ) -> None:
        # If canvas is not a Canvas but a widget, create a Canvas
        if not isinstance(canvas, tk.Canvas):
            frame = tk.Frame(canvas, bg="black")
            frame.pack(pady=10, fill=tk.X)
            self.canvas = tk.Canvas(frame, width=400, height=400, bg="black", highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas = canvas

        # Handle canvas size for positioning
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600

        # Default center position if not specified
        if x is None:
            x = canvas_width // 2
        if y is None:
            y = canvas_height // 2

        self.x = x
        self.y = y
        self.min_radius = min_radius
        self.max_radius = max_radius

        # Handle theme if provided
        if theme is not None:
            if isinstance(theme, str):
                theme_obj = get_theme(theme)
            else:
                theme_obj = theme
            self.color = theme_obj.accent_color
        else:
            self.color = color

        self.current_radius = min_radius
        self.pulse_speed = pulse_speed
        self.growing = True
        self.circle_id = self.canvas.create_oval(
            x - min_radius,
            y - min_radius,
            x + min_radius,
            y + min_radius,
            fill=self.color,
            outline="",
        )
        self.running = False

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

        # Update circle size
        self.canvas.coords(
            self.circle_id,
            self.x - self.current_radius,
            self.y - self.current_radius,
            self.x + self.current_radius,
            self.y + self.current_radius,
        )

        self.canvas.after(20, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False
        # Reset to minimum size
        self.canvas.coords(
            self.circle_id,
            self.x - self.min_radius,
            self.y - self.min_radius,
            self.x + self.min_radius,
            self.y + self.min_radius,
        )


class HexagonGrid:
    """Animated hexagonal grid for UI backgrounds.

    This component creates a grid of hexagons that can pulse or change visibility
    for a futuristic background effect.

    Args:
        canvas: The tkinter canvas or widget to draw on
        size: Size of each hexagon
        gap: Gap between hexagons
        color: Color of the hexagons
        alpha: Opacity level for hexagons (0.0-1.0) - controls visual intensity
        theme: Optional UITheme instance or theme name
    """

    def __init__(
        self,
        canvas: Union[tk.Canvas, tk.Widget],
        size: int = 40,
        gap: int = 10,
        color: str = UI_BLUE,
        alpha: float = 0.2,
        theme: Optional[Union[UITheme, str]] = None,
    ) -> None:
        # If canvas is not a Canvas but a widget, create a Canvas
        if not isinstance(canvas, tk.Canvas):
            frame = tk.Frame(canvas, bg="black")
            frame.pack(pady=10, fill=tk.X)
            self.canvas = tk.Canvas(frame, width=800, height=200, bg="black", highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas = canvas

        self.size = size
        self.gap = gap

        # Handle theme if provided
        if theme is not None:
            if isinstance(theme, str):
                theme_obj = get_theme(theme)
            else:
                theme_obj = theme
            self.color = theme_obj.accent_color
        else:
            self.color = color

        self.alpha = alpha  # Used conceptually for brightness/intensity
        self.hexagons: List[HexagonData] = []
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

                # Draw hexagon - use base color without alpha (not supported in Tkinter)
                hex_id = self.canvas.create_polygon(points, fill="", outline=self.color, width=1)

                # Store hexagon info
                self.hexagons.append(
                    HexagonData(
                        id=hex_id,
                        points=points,
                        pulse=random.random(),
                        pulse_speed=random.uniform(0.01, 0.05),
                        brightness=random.uniform(0.1, 0.3),
                    )
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
            hex_data.pulse = (hex_data.pulse + hex_data.pulse_speed) % 1.0

            # Toggle visibility occasionally
            if random.random() < 0.05:  # 5% chance to toggle visibility
                current_state = self.canvas.itemcget(hex_data.id, "state")
                new_state = "hidden" if current_state == "normal" else "normal"
                self.canvas.itemconfig(hex_data.id, state=new_state)

        self.canvas.after(50, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False


class ScanLine:
    """Animated scan line effect for UI interfaces.

    This component creates a horizontal line that scans from top to bottom
    of the canvas, creating a scanning effect.

    Args:
        canvas: The tkinter canvas or widget to draw on
        color: Color of the scan line
        speed: Speed of the scanning animation
        thickness: Thickness of the scan line
        theme: Optional UITheme instance or theme name
    """

    def __init__(
        self,
        canvas: Union[tk.Canvas, tk.Widget],
        color: str = UI_BLUE,
        speed: int = 2,
        thickness: int = 3,
        theme: Optional[Union[UITheme, str]] = None,
    ) -> None:
        # If canvas is not a Canvas but a widget, create a Canvas
        if not isinstance(canvas, tk.Canvas):
            frame = tk.Frame(canvas, bg="black")
            frame.pack(pady=10, fill=tk.X)
            self.canvas = tk.Canvas(frame, width=800, height=200, bg="black", highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas = canvas

        # Handle theme if provided
        if theme is not None:
            if isinstance(theme, str):
                theme_obj = get_theme(theme)
            else:
                theme_obj = theme
            self.color = theme_obj.accent_color
        else:
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
    """Target lock animation for UI interfaces.

    This component creates a targeting reticle animation that can be
    used to highlight or focus on a particular point.

    Args:
        canvas: The tkinter canvas or widget to draw on
        x: X-coordinate of the target center
        y: Y-coordinate of the target center
        size: Size of the targeting reticle
        color: Color of the reticle
        theme: Optional UITheme instance or theme name
    """

    def __init__(
        self,
        canvas: Union[tk.Canvas, tk.Widget],
        x: int = None,
        y: int = None,
        size: int = 50,
        color: str = DANGER_RED,
        theme: Optional[Union[UITheme, str]] = None,
    ) -> None:
        # If canvas is not a Canvas but a widget, create a Canvas
        if not isinstance(canvas, tk.Canvas):
            frame = tk.Frame(canvas, bg="black")
            frame.pack(pady=10, fill=tk.X)
            self.canvas = tk.Canvas(frame, width=400, height=400, bg="black", highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas = canvas

        # Handle canvas size for positioning
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600

        # Default center position if not specified
        if x is None:
            x = canvas_width // 2
        if y is None:
            y = canvas_height // 2

        self.x = x
        self.y = y
        self.size = size

        # Handle theme if provided
        if theme is not None:
            if isinstance(theme, str):
                theme_obj = get_theme(theme)
            else:
                theme_obj = theme
            self.color = theme_obj.error_color
        else:
            self.color = color

        self.shape_ids: List[int] = []
        self.running = False
        self.rotation = 0

        self._create_shapes()

    def _create_shapes(self) -> None:
        """Create the targeting shapes"""
        # Outer circle
        self.shape_ids.append(
            self.canvas.create_oval(
                self.x - self.size,
                self.y - self.size,
                self.x + self.size,
                self.y + self.size,
                outline=self.color,
                width=2,
                dash=(3, 2),
            )
        )

        # Inner circle
        inner_size = self.size * 0.6
        self.shape_ids.append(
            self.canvas.create_oval(
                self.x - inner_size,
                self.y - inner_size,
                self.x + inner_size,
                self.y + inner_size,
                outline=self.color,
                width=1,
            )
        )

        # Center dot
        dot_size = self.size * 0.1
        self.shape_ids.append(
            self.canvas.create_oval(
                self.x - dot_size,
                self.y - dot_size,
                self.x + dot_size,
                self.y + dot_size,
                fill=self.color,
                outline="",
            )
        )

        # Crosshairs
        line_length = self.size * 0.8
        # Horizontal lines
        self.shape_ids.append(
            self.canvas.create_line(
                self.x - line_length,
                self.y,
                self.x - self.size * 0.2,
                self.y,
                fill=self.color,
                width=2,
            )
        )
        self.shape_ids.append(
            self.canvas.create_line(
                self.x + self.size * 0.2,
                self.y,
                self.x + line_length,
                self.y,
                fill=self.color,
                width=2,
            )
        )
        # Vertical lines
        self.shape_ids.append(
            self.canvas.create_line(
                self.x,
                self.y - line_length,
                self.x,
                self.y - self.size * 0.2,
                fill=self.color,
                width=2,
            )
        )
        self.shape_ids.append(
            self.canvas.create_line(
                self.x,
                self.y + self.size * 0.2,
                self.x,
                self.y + line_length,
                fill=self.color,
                width=2,
            )
        )

    def start(self) -> None:
        """Start the target lock animation"""
        self.running = True
        self._animate()

    def _animate(self) -> None:
        """Animate the target lock"""
        if not self.running:
            return

        # Rotate the dashed line
        self.rotation = (self.rotation + 2) % 360
        self.canvas.itemconfig(self.shape_ids[0], dash=(3, 2, 1, 2), dashoffset=self.rotation)

        self.canvas.after(50, self._animate)

    def stop(self) -> None:
        """Stop the animation"""
        self.running = False
        for shape_id in self.shape_ids:
            self.canvas.itemconfig(shape_id, state="normal")

    def set_position(self, x: int, y: int) -> None:
        """Move the target lock to a new position"""
        dx = x - self.x
        dy = y - self.y
        for shape_id in self.shape_ids:
            self.canvas.move(shape_id, dx, dy)
        self.x = x
        self.y = y
