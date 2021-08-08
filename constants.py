from aqt.qt import *

AUTO_SYNC_CONFIG_NAME = "auto_sync_config"

CONFIG_SYNC_TIMEOUT = "sync timeout"
CONFIG_IDLE_SYNC_TIMEOUT = "idle sync timeout"
CONFIG_CONFIG_VERSION = "config version"
CONFIG_STRICT_BACKGROUND_MODE = "strict background mode"

CONFIG_DEFAULT_CONFIG = {CONFIG_SYNC_TIMEOUT: 1, CONFIG_IDLE_SYNC_TIMEOUT: 10, CONFIG_CONFIG_VERSION: 1, CONFIG_STRICT_BACKGROUND_MODE: True}

AUTO_SYNC_ICON = QApplication.instance().style().standardIcon(QStyle.SP_BrowserReload)
