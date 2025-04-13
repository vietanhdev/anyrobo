"""JARVIS-inspired UI components for anyrobo."""

from anyrobo.ui.animations import (
    CircularProgressAnimation,
    HexagonGrid,
    PulsatingCircle,
    ScanLine,
    TargetLock,
)
from anyrobo.ui.components import FuturisticButton, StatusBar, TextDisplay

# from anyrobo.ui.graphical_ui import GraphicalUIHandler, run_graphical_ui
from anyrobo.ui.themes import (
    DangerTheme,
    GLaDOSTheme,
    HolographicTheme,
    JarvisTheme,
    UITheme,
    get_theme,
    register_theme,
)
from anyrobo.ui.visualizers import AudioVisualizer, LiveAudioVisualizer

__all__ = [
    # Main UI
    "JarvisUI",
    "run_jarvis_ui",
    # GraphicalUI integration
    # "GraphicalUIHandler",
    # "run_graphical_ui",
    # Animations
    "CircularProgressAnimation",
    "HexagonGrid",
    "ScanLine",
    "PulsatingCircle",
    "TargetLock",
    # Visualizers
    "AudioVisualizer",
    "LiveAudioVisualizer",
    # Components
    "FuturisticButton",
    "StatusBar",
    "TextDisplay",
    # Themes
    "UITheme",
    "JarvisTheme",
    "DangerTheme",
    "GLaDOSTheme",
    "HolographicTheme",
    "get_theme",
    "register_theme",
]
