import os
import json
import logging
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configs"
LOG_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"
RECORDINGS_DIR = BASE_DIR / "recordings"

# Ensure directories exist
for directory in [CONFIG_DIR, LOG_DIR, ASSETS_DIR, RECORDINGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.json"
USER_CONFIG_PATH = CONFIG_DIR / "user_settings.json"


class ConfigManager:
    """
    Manages loading, saving, and updating application configuration.
    """
    def __init__(self):
        self.settings = self._load_default_settings()
        self.load_user_settings()

    def _load_default_settings(self) -> dict:
        """Returns the hardcoded default settings as a fallback."""
        return {
            "camera": {
                "index": 0,
                "width": 640,
                "height": 480,
                "fps": 30
            },
            "steering": {
                "sensitivity": 1.0,
                "dead_zone": 5,
                "max_angle": 90,
                "smoothing_method": "ema",
                "alpha": 0.3
            },
            "gestures": {
                "enabled": True,
                "brake_threshold": 0.8
            },
            "voice": {
                "enabled": False,
                "language": "en-US"
            },
            "gui": {
                "theme": "dark",
                "show_dashboard": True,
                "lane_assist": False
            }
        }

    def load_user_settings(self):
        """Loads user settings from JSON if it exists, otherwise uses defaults."""
        if USER_CONFIG_PATH.exists():
            try:
                with open(USER_CONFIG_PATH, "r") as f:
                    user_settings = json.load(f)
                    # Deep update settings (basic implementation)
                    for key, val in user_settings.items():
                        if isinstance(val, dict) and key in self.settings:
                            self.settings[key].update(val)
                        else:
                            self.settings[key] = val
            except Exception as e:
                logging.error(f"Failed to load user settings: {e}")

    def save_settings(self):
        """Saves the current settings to the user configuration JSON file."""
        try:
            with open(USER_CONFIG_PATH, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save user settings: {e}")

    def get(self, section: str, key: str = None):
        """Retrieves a specific setting."""
        if key:
            return self.settings.get(section, {}).get(key)
        return self.settings.get(section)

    def set(self, section: str, key: str, value):
        """Updates a specific setting."""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value
        self.save_settings()


# Global config instance
config = ConfigManager()
