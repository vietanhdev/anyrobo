"""Animation components for the anyrobo UI system."""

import math
import random

# UI colors
UI_BLUE = "#00FFFF"
UI_DARK_BLUE = "#001831"
BG_COLOR = "#000A14"
DANGER_RED = "#FF3030"
WARNING_YELLOW = "#FFDD00"


class CircularProgressAnimation:
    """Animated circular progress indicator for UI interfaces.

    This component creates a circular progress animation that can be used
    to indicate loading or processing states.

    Args:
        canvas: The tkinter canvas to draw on
        x: X-coordinate of the center of the animation
        y: Y-coordinate of the center of the animation
        size: Diameter of the circle
        color: Color of the progress arc
        bg_color: Background circle color
        width: Line width of the circle
    """

    def __init__(self, canvas, x, y, size=100, color="#5CE1E6", bg_color="#002137", width=8):
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
        self.arc_id = None
        self.bg_id = None

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

    def start(self):
        """Start the animation"""
        self.running = True
        self._animate()

    def _animate(self):
        """Animate the progress indicator"""
        if not self.running:
            return

        if self.arc_id:
            self.canvas.delete(self.arc_id)

        start_angle = self.angle
        end_angle = (self.angle + self.arc_length) % 360

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

    def stop(self):
        """Stop the animation"""
        self.running = False
        if self.arc_id:
            self.canvas.delete(self.arc_id)
            self.arc_id = None


class PulsatingCircle:
    """Pulsating circle animation for UI interfaces.

    This component creates a circle that pulses between a minimum and maximum size.

    Args:
        canvas: The tkinter canvas to draw on
        x: X-coordinate of the center of the circle
        y: Y-coordinate of the center of the circle
        min_radius: Minimum radius of the circle
        max_radius: Maximum radius of the circle
        color: Color of the circle
        pulse_speed: Speed of the pulsating effect
    """

    def __init__(
        self, canvas, x, y, min_radius=20, max_radius=30, color="#5CE1E6", pulse_speed=0.05
    ):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.current_radius = min_radius
        self.color = color
        self.pulse_speed = pulse_speed
        self.growing = True
        self.circle_id = None
        self.running = False

        # Create initial circle
        self.circle_id = canvas.create_oval(
            x - min_radius, y - min_radius, x + min_radius, y + min_radius, fill=color, outline=""
        )

    def start(self):
        """Start the pulsating animation"""
        self.running = True
        self._animate()

    def _animate(self):
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

    def stop(self):
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
        canvas: The tkinter canvas to draw on
        size: Size of each hexagon
        gap: Gap between hexagons
        color: Color of the hexagons
        alpha: Transparency of the hexagons (not fully supported in Tkinter)
    """

    def __init__(self, canvas, size=40, gap=10, color=UI_BLUE, alpha=0.2):
        self.canvas = canvas
        self.size = size
        self.gap = gap
        self.color = color
        self.alpha = alpha
        self.hexagons = []
        self.running = False
        self.create_grid()

    def create_grid(self):
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

                # Draw hexagon
                hex_id = self.canvas.create_polygon(points, fill="", outline=self.color, width=1)

                # Store hexagon info
                self.hexagons.append(
                    {
                        "id": hex_id,
                        "points": points,
                        "pulse": random.random(),
                        "pulse_speed": random.uniform(0.01, 0.05),
                        "brightness": random.uniform(0.1, 0.3),
                    }
                )

    def start(self):
        """Start the animation"""
        self.running = True
        self._animate()

    def _animate(self):
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

    def stop(self):
        """Stop the animation"""
        self.running = False


class ScanLine:
    """Animated scan line effect for UI interfaces.

    This component creates a horizontal line that scans from top to bottom
    of the canvas, creating a scanning effect.

    Args:
        canvas: The tkinter canvas to draw on
        color: Color of the scan line
        speed: Speed of the scanning animation
        thickness: Thickness of the scan line
    """

    def __init__(self, canvas, color=UI_BLUE, speed=2, thickness=3):
        self.canvas = canvas
        self.color = color
        self.speed = speed
        self.thickness = thickness
        self.position = 0
        self.scan_id = None
        self.running = False

    def start(self):
        """Start the scan line animation"""
        self.running = True
        self._animate()

    def _animate(self):
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

    def stop(self):
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
        canvas: The tkinter canvas to draw on
        x: X-coordinate of the target center
        y: Y-coordinate of the target center
        size: Size of the targeting reticle
        color: Color of the reticle
    """

    def __init__(self, canvas, x, y, size=50, color=DANGER_RED):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.shape_ids = []
        self.running = False
        self.rotation = 0

        self._create_shapes()

    def _create_shapes(self):
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

    def start(self):
        """Start the target lock animation"""
        self.running = True
        self._animate()

    def _animate(self):
        """Animate the target lock"""
        if not self.running:
            return

        # Rotate the dashed line
        self.rotation = (self.rotation + 2) % 360
        self.canvas.itemconfig(self.shape_ids[0], dash=(3, 2, 1, 2), dashoffset=self.rotation)

        self.canvas.after(50, self._animate)

    def stop(self):
        """Stop the animation"""
        self.running = False
        for shape_id in self.shape_ids:
            self.canvas.itemconfig(shape_id, state="normal")

    def set_position(self, x, y):
        """Move the target lock to a new position"""
        dx = x - self.x
        dy = y - self.y
        for shape_id in self.shape_ids:
            self.canvas.move(shape_id, dx, dy)
        self.x = x
        self.y = y
