import yaml
import logging
import os
import sys

logger = logging.getLogger(__name__)
class SettingsReader:
    def __init__(self, config_path: str = 'config/settings.yaml'):
        self.config_path = config_path
        self.settings = self.load_settings()
        logger.info(f"Settings loaded from {config_path}")
    
    def load_settings(self) -> dict:
        if not os.path.exists(self.config_path):
            logger.error(f"Config file {self.config_path} not found")
            raise FileNotFoundError(f"Config file {self.config_path} not found")

        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)

    def get_base_path(self) -> str:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))