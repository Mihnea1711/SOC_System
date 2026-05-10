import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = BASE_DIR / "config.yaml"

class Config:
    def __init__(self):
        self._config = self._load_yaml()

    def _load_yaml(self):
        if not CONFIG_FILE.exists():
            return {}
        with open(CONFIG_FILE, 'r') as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as exc:
                print(f"Error parsing config file: {exc}")
                return {}

    def __getattr__(self, item):
        """
        Allows accessing top-level config keys as attributes.
        Example: settings.app or settings.kafka
        """
        if item in self._config:
            return self._config[item]
        raise AttributeError(f"'Config' object has no attribute '{item}'")

    def __str__(self):
        """Returns a readable string representation of the configuration."""
        return f"Config(\n{yaml.dump(self._config, default_flow_style=False).strip()}\n)"

# Create a singleton instance to be imported across the app
settings = Config()