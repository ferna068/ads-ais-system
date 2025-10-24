import yaml
import logging
import os

logger = logging.getLogger(__name__)
base_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_path, '../../config/settings.yaml')

class SettingsReader:
    def __init__(self, config_path: str = config_path):
        self.config_path = config_path
        self.settings = self.load_settings()
        logger.info(f"Settings loaded from {config_path}")
    
    def load_settings(self) -> dict:
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)