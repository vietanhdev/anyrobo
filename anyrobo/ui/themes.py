"""Theme definitions for anyrobo UI components."""

from typing import Dict, Tuple


# Common UI color schemes
class UITheme:
    """Base class for UI themes.

    This defines the core colors and appearance settings for a UI theme.
    Subclasses should override the color properties to define specific themes.
    """

    @property
    def primary_color(self) -> str:
        """Primary UI color"""
        return "#00FFFF"  # Cyan

    @property
    def secondary_color(self) -> str:
        """Secondary UI color"""
        return "#4682B4"  # Steel blue

    @property
    def accent_color(self) -> str:
        """Accent UI color"""
        return "#87CEFA"  # Light sky blue

    @property
    def background_color(self) -> str:
        """Background color"""
        return "#000A14"  # Dark blue

    @property
    def surface_color(self) -> str:
        """Surface color for panels/cards"""
        return "#001831"  # Dark blue

    @property
    def text_color(self) -> str:
        """Main text color"""
        return "#FFFFFF"  # White

    @property
    def secondary_text_color(self) -> str:
        """Secondary text color"""
        return "#AAAAAA"  # Light gray

    @property
    def warning_color(self) -> str:
        """Warning color"""
        return "#FFDD00"  # Yellow

    @property
    def error_color(self) -> str:
        """Error/danger color"""
        return "#FF3030"  # Red

    @property
    def success_color(self) -> str:
        """Success color"""
        return "#39FF14"  # Green

    @property
    def button_fonts(self) -> Tuple:
        """Font configuration for buttons"""
        return ("Helvetica", 10, "bold")

    @property
    def title_fonts(self) -> Tuple:
        """Font configuration for titles"""
        return ("Helvetica", 24, "bold")

    @property
    def text_fonts(self) -> Tuple:
        """Font configuration for regular text"""
        return ("Courier", 12)

    @property
    def status_fonts(self) -> Tuple:
        """Font configuration for status text"""
        return ("Helvetica", 9)

    def get_all_colors(self) -> Dict[str, str]:
        """Get all theme colors as a dictionary"""
        return {
            "primary": self.primary_color,
            "secondary": self.secondary_color,
            "accent": self.accent_color,
            "background": self.background_color,
            "surface": self.surface_color,
            "text": self.text_color,
            "secondary_text": self.secondary_text_color,
            "warning": self.warning_color,
            "error": self.error_color,
            "success": self.success_color,
        }


class JarvisTheme(UITheme):
    """JARVIS-inspired UI theme.

    This theme uses blue and cyan colors for a futuristic sci-fi look
    inspired by the JARVIS AI from the Iron Man movies.
    """

    @property
    def primary_color(self) -> str:
        return "#1E90FF"  # Royal blue

    @property
    def secondary_color(self) -> str:
        return "#4682B4"  # Steel blue

    @property
    def accent_color(self) -> str:
        return "#87CEFA"  # Light sky blue

    @property
    def background_color(self) -> str:
        return "#0A192F"  # Dark blue

    @property
    def surface_color(self) -> str:
        return "#0A1F33"  # Slightly lighter dark blue


class DangerTheme(UITheme):
    """Danger/Combat UI theme.

    This theme uses red and orange colors for a warning/danger look
    suitable for critical or combat interfaces.
    """

    @property
    def primary_color(self) -> str:
        return "#FF3030"  # Red

    @property
    def secondary_color(self) -> str:
        return "#FF7700"  # Orange

    @property
    def accent_color(self) -> str:
        return "#FFDD00"  # Yellow

    @property
    def background_color(self) -> str:
        return "#0A0A0A"  # Very dark gray

    @property
    def surface_color(self) -> str:
        return "#1A0A0A"  # Dark red-tinted surface


class GLaDOSTheme(UITheme):
    """GLaDOS-inspired UI theme.

    This theme uses whites, grays and pale cyan colors for a clean,
    clinical look inspired by the GLaDOS AI from the Portal games.
    """

    @property
    def primary_color(self) -> str:
        return "#00F0F0"  # Brighter cyan

    @property
    def secondary_color(self) -> str:
        return "#CCCCCC"  # Light gray

    @property
    def accent_color(self) -> str:
        return "#F7F7F7"  # Off-white

    @property
    def background_color(self) -> str:
        return "#1F1F1F"  # Dark gray

    @property
    def surface_color(self) -> str:
        return "#2A2A2A"  # Medium gray

    @property
    def text_color(self) -> str:
        return "#F0F0F0"  # Off-white

    @property
    def secondary_text_color(self) -> str:
        return "#AAAAAA"  # Light gray


class HolographicTheme(UITheme):
    """Holographic UI theme.

    This theme uses teals and blue-greens for a holographic appearance
    with semi-transparency and glowing effects.
    """

    @property
    def primary_color(self) -> str:
        return "#00FFCC"  # Bright teal

    @property
    def secondary_color(self) -> str:
        return "#00CCAA"  # Medium teal

    @property
    def accent_color(self) -> str:
        return "#80FFD4"  # Light teal

    @property
    def background_color(self) -> str:
        return "#081414"  # Very dark teal

    @property
    def surface_color(self) -> str:
        return "#102020"  # Dark teal


# Theme registry
_THEMES = {
    "jarvis": JarvisTheme(),
    "danger": DangerTheme(),
    "glados": GLaDOSTheme(),
    "holographic": HolographicTheme(),
    "default": UITheme(),
}


def get_theme(theme_name: str = "default") -> UITheme:
    """Get a UI theme by name.

    Args:
        theme_name: Name of the theme to retrieve

    Returns:
        UITheme instance
    """
    return _THEMES.get(theme_name.lower(), _THEMES["default"])


def register_theme(name: str, theme: UITheme) -> None:
    """Register a custom theme.

    Args:
        name: Theme name
        theme: UITheme instance
    """
    _THEMES[name.lower()] = theme
