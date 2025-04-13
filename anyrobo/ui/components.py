"""Common UI components for the anyrobo UI system."""

import time
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional, Union

from anyrobo.ui.themes import UITheme, get_theme

# UI colors (fallback values, themes should be preferred)
UI_BLUE = "#00FFFF"
UI_DARK_BLUE = "#001831"
BG_COLOR = "#000A14"
DANGER_RED = "#FF3030"
WARNING_YELLOW = "#FFDD00"


class FuturisticButton:
    """A futuristic-looking button for UI interfaces.

    This creates a stylized button with hover effects and custom styling.

    Args:
        parent: Parent tkinter widget
        text: Button text
        command: Function to call when button is clicked
        theme: UITheme instance or theme name to use for styling
        width: Button width
        height: Button height
        font: Button font
    """

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "Button",
        command: Optional[Callable[[], None]] = None,
        theme: Optional[Union[UITheme, str]] = None,
        width: int = 120,
        height: int = 40,
        font: Optional[Any] = None,
    ) -> None:
        self.parent = parent
        self.text = text
        self.command = command
        self.width = width
        self.height = height

        # Get theme
        if isinstance(theme, UITheme):
            self.theme = theme
        elif isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = get_theme("default")

        # Set colors from theme
        self.bg_color = self.theme.primary_color
        self.fg_color = self.theme.text_color
        self.hover_color = self.theme.accent_color

        # Set font from theme if not provided
        self.font = font or self.theme.button_fonts

        # Create canvas for the button
        self.canvas = tk.Canvas(
            parent, width=width, height=height, bg=self.theme.background_color, highlightthickness=0
        )

        # Create button elements
        self.create_button()

        # Bind events
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)

    def create_button(self) -> None:
        """Create the button elements"""
        # Main button rectangle
        self.button = self.canvas.create_rectangle(
            2,
            2,
            self.width - 2,
            self.height - 2,
            fill=self.theme.background_color,
            outline=self.bg_color,
            width=2,
        )

        # Button text
        self.button_text = self.canvas.create_text(
            self.width / 2, self.height / 2, text=self.text, fill=self.fg_color, font=self.font
        )

        # Corner accents
        accent_size = 6
        # Top-left
        self.corner_tl = self.canvas.create_line(
            [0, accent_size, 0, 0, accent_size, 0], fill=self.bg_color, width=2
        )
        # Top-right
        self.corner_tr = self.canvas.create_line(
            [self.width - accent_size, 0, self.width, 0, self.width, accent_size],
            fill=self.bg_color,
            width=2,
        )
        # Bottom-left
        self.corner_bl = self.canvas.create_line(
            [0, self.height - accent_size, 0, self.height, accent_size, self.height],
            fill=self.bg_color,
            width=2,
        )
        # Bottom-right
        self.corner_br = self.canvas.create_line(
            [
                self.width - accent_size,
                self.height,
                self.width,
                self.height,
                self.width,
                self.height - accent_size,
            ],
            fill=self.bg_color,
            width=2,
        )

        # Store corner IDs for later access
        self.corner_ids = [self.corner_tl, self.corner_tr, self.corner_bl, self.corner_br]

    def on_enter(self, event: Any) -> None:
        """Handle mouse enter event"""
        self.canvas.itemconfig(self.button, outline=self.hover_color)
        for item in self.corner_ids:
            self.canvas.itemconfig(item, fill=self.hover_color)

    def on_leave(self, event: Any) -> None:
        """Handle mouse leave event"""
        self.canvas.itemconfig(self.button, outline=self.bg_color)
        for item in self.corner_ids:
            self.canvas.itemconfig(item, fill=self.bg_color)

    def on_click(self, event: Any) -> None:
        """Handle mouse click event"""
        if self.command is not None:
            self.command()

    def update_theme(self, theme: Union[UITheme, str]) -> None:
        """Update the button's theme

        Args:
            theme: UITheme instance or theme name
        """
        if isinstance(theme, UITheme):
            self.theme = theme
        else:
            self.theme = get_theme(theme)

        # Update colors
        self.bg_color = self.theme.primary_color
        self.fg_color = self.theme.text_color
        self.hover_color = self.theme.accent_color

        # Update appearance
        self.canvas.config(bg=self.theme.background_color)
        self.canvas.itemconfig(self.button, fill=self.theme.background_color, outline=self.bg_color)
        self.canvas.itemconfig(self.button_text, fill=self.fg_color)

        for item in self.corner_ids:
            self.canvas.itemconfig(item, fill=self.bg_color)

    def pack(self, **kwargs: Any) -> None:
        """Pack the button canvas"""
        self.canvas.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """Grid the button canvas"""
        self.canvas.grid(**kwargs)

    def place(self, **kwargs: Any) -> None:
        """Place the button canvas"""
        self.canvas.place(**kwargs)


class StatusBar:
    """Status bar for UI interfaces.

    This creates a status bar with clock, status message, and warning display.

    Args:
        parent: Parent tkinter widget
        theme: UITheme instance or theme name
        height: Height of the status bar
        font: Status bar font
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Optional[Union[UITheme, str]] = None,
        height: int = 30,
        font: Optional[Any] = None,
    ) -> None:
        self.parent = parent

        # Get theme
        if isinstance(theme, UITheme):
            self.theme = theme
        elif isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = get_theme("default")

        # Set colors from theme
        self.bg_color = self.theme.background_color
        self.fg_color = self.theme.primary_color
        self.warning_color = self.theme.warning_color

        self.height = height
        self.font = font or self.theme.status_fonts

        # Create frame
        self.frame = tk.Frame(parent, bg=self.bg_color, height=height)

        # Create elements
        self.create_status_elements()

        # Start clock
        self.update_clock()

    def create_status_elements(self) -> None:
        """Create the status bar elements"""
        # Left status indicator
        self.status_left = tk.Label(
            self.frame, text="Status: Online", font=self.font, fg=self.fg_color, bg=self.bg_color
        )
        self.status_left.pack(side=tk.LEFT)

        # Center indicator for warnings
        self.status_center = tk.Label(
            self.frame, text="", font=self.font, fg=self.warning_color, bg=self.bg_color
        )
        self.status_center.pack(side=tk.LEFT, padx=20)

        # Right status with time
        self.status_right = tk.Label(
            self.frame,
            text="",
            font=self.font,
            fg=self.theme.secondary_text_color,
            bg=self.bg_color,
        )
        self.status_right.pack(side=tk.RIGHT)

    def update_theme(self, theme: Union[UITheme, str]) -> None:
        """Update the status bar's theme

        Args:
            theme: UITheme instance or theme name
        """
        if isinstance(theme, UITheme):
            self.theme = theme
        else:
            self.theme = get_theme(theme)

        # Update colors
        self.bg_color = self.theme.background_color
        self.fg_color = self.theme.primary_color
        self.warning_color = self.theme.warning_color

        # Update appearance
        self.frame.config(bg=self.bg_color)
        self.status_left.config(fg=self.fg_color, bg=self.bg_color)
        self.status_center.config(fg=self.warning_color, bg=self.bg_color)
        self.status_right.config(fg=self.theme.secondary_text_color, bg=self.bg_color)

    def update_clock(self) -> None:
        """Update the clock in the status bar"""
        current_time = time.strftime("%H:%M:%S")
        self.status_right.config(text=f"System Time: {current_time}")

        # Schedule next update
        self.parent.after(1000, self.update_clock)

    def set_status(self, text: str) -> None:
        """Update the status text"""
        self.status_left.config(text=f"Status: {text}")

    def set_warning(self, text: str) -> None:
        """Set warning text in status bar"""
        self.status_center.config(text=text)

    def pack(self, **kwargs: Any) -> None:
        """Pack the status bar frame"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """Grid the status bar frame"""
        self.frame.grid(**kwargs)

    def place(self, **kwargs: Any) -> None:
        """Place the status bar frame"""
        self.frame.place(**kwargs)


class TextDisplay:
    """Text display area for UI interfaces.

    This creates a text display area with scrollbar and tag-based formatting.

    Args:
        parent: Parent tkinter widget
        theme: UITheme instance or theme name
        font: Text font
        height: Height of the text area in lines
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Optional[Union[UITheme, str]] = None,
        font: Optional[Any] = None,
        height: int = 10,
    ) -> None:
        self.parent = parent

        # Get theme
        if isinstance(theme, UITheme):
            self.theme = theme
        elif isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = get_theme("default")

        # Set colors from theme
        self.bg_color = self.theme.surface_color
        self.fg_color = self.theme.text_color
        self.accent_color = self.theme.primary_color

        self.font = font or self.theme.text_fonts
        self.height = height

        # Create frame
        self.frame = tk.Frame(parent, bg=self.bg_color, padx=10, pady=10)

        # Make text frame have a colored border
        self.frame.config(highlightbackground=self.accent_color, highlightthickness=2)

        # Create elements
        self.create_text_display()

    def create_text_display(self) -> None:
        """Create the text display area"""
        self.text = tk.Text(
            self.frame,
            bg=self.bg_color,
            fg=self.fg_color,
            font=self.font,
            wrap=tk.WORD,
            height=self.height,
            bd=0,
            padx=5,
            pady=5,
            insertbackground=self.accent_color,  # Cursor color
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.text, command=self.text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=scrollbar.set)

        # Configure tags
        self.text.tag_configure("system", foreground=self.accent_color)
        self.text.tag_configure("user", foreground=self.fg_color)
        self.text.tag_configure("warning", foreground=self.theme.warning_color)
        self.text.tag_configure("error", foreground=self.theme.error_color)

    def update_theme(self, theme: Union[UITheme, str]) -> None:
        """Update the text display's theme

        Args:
            theme: UITheme instance or theme name
        """
        if isinstance(theme, UITheme):
            self.theme = theme
        else:
            self.theme = get_theme(theme)

        # Update colors
        self.bg_color = self.theme.surface_color
        self.fg_color = self.theme.text_color
        self.accent_color = self.theme.primary_color

        # Update appearance
        self.frame.config(bg=self.bg_color, highlightbackground=self.accent_color)
        self.text.config(bg=self.bg_color, fg=self.fg_color, insertbackground=self.accent_color)

        # Update tags
        self.text.tag_configure("system", foreground=self.accent_color)
        self.text.tag_configure("user", foreground=self.fg_color)
        self.text.tag_configure("warning", foreground=self.theme.warning_color)
        self.text.tag_configure("error", foreground=self.theme.error_color)

    def add_system_text(self, text: str, system_name: str = "System") -> None:
        """Add text from the system to the display"""
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, f"{system_name}: ", "system")
        self.text.insert(tk.END, f"{text}\n\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def add_user_text(self, text: str) -> None:
        """Add user text to the display"""
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, "User: ", "user")
        self.text.insert(tk.END, f"{text}\n\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def add_text(self, text: str, tag: Optional[str] = None) -> None:
        """Add text with optional formatting"""
        self.text.config(state=tk.NORMAL)
        if tag:
            self.text.insert(tk.END, f"{text}\n\n", tag)
        else:
            self.text.insert(tk.END, f"{text}\n\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def clear(self) -> None:
        """Clear all text"""
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)

    def pack(self, **kwargs: Any) -> None:
        """Pack the text display frame"""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """Grid the text display frame"""
        self.frame.grid(**kwargs)

    def place(self, **kwargs: Any) -> None:
        """Place the text display frame"""
        self.frame.place(**kwargs)
