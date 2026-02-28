from dataclasses import dataclass

@dataclass
class AppConfig:
    """Global UI/app settings only.
    Never mixed with battle mechanics.
    Will be saved to settings.json in Phase 4 (separate from build saves)."""
    appearance_mode: str = "dark"      # "dark" / "light" / "system"
    color_theme: str = "dark-blue"     # any valid customtkinter theme