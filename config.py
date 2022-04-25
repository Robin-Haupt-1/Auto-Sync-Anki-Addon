from aqt import mw
from .constants import AUTO_SYNC_CONFIG_NAME, CONFIG_DEFAULT_CONFIG


class AutoSyncConfigManager:
    """Manages accessing the addons configuration in Ankis config storage"""

    def __init__(self, mw: mw):
        """Load the config with default return value and in case it's the first run, save it to Anki"""
        self.mw = mw
        self.col = mw.col
        self.config = self.col.get_config(AUTO_SYNC_CONFIG_NAME, default=CONFIG_DEFAULT_CONFIG)
        self.col.set_config(AUTO_SYNC_CONFIG_NAME, self.config)

    def get(self, key):
        """get the value of the given config key"""
        return self.config[key]

    def set(self, key, val):
        """get the value of the given config key"""
        self.config[key] = val
        self.col.set_config(AUTO_SYNC_CONFIG_NAME, self.config)
