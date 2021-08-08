from aqt import mw
from .constants import AUTO_SYNC_CONFIG_NAME, CONFIG_DEFAULT_CONFIG


class AutoSyncConfigManager:
    def __init__(self, mw: mw):
        self.mw = mw
        self.col = mw.col
        self.config = self.col.get_config(AUTO_SYNC_CONFIG_NAME, default=CONFIG_DEFAULT_CONFIG)
        self.col.set_config(AUTO_SYNC_CONFIG_NAME, self.config)

    def get_config(self):
        return self.config

    def get(self, key):
        return self.config[key]

    def set(self, key, val):
        self.config[key] = val
        self.col.set_config(AUTO_SYNC_CONFIG_NAME, self.config)

    def reset_config(self):
        self.col.set_config(AUTO_SYNC_CONFIG_NAME, CONFIG_DEFAULT_CONFIG)
        self.config = self.col.get_config(AUTO_SYNC_CONFIG_NAME)
