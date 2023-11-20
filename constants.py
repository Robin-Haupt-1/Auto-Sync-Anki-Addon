from aqt.qt import QApplication, QStyle

# Config parameter keys and default values

AUTO_SYNC_CONFIG_NAME = "auto_sync_config"
CONFIG_SYNC_TIMEOUT = "sync timeout"
CONFIG_IDLE_SYNC_TIMEOUT = "idle sync timeout"
CONFIG_CONFIG_VERSION = "config version"
CONFIG_STRICTLY_AVOID_INTERRUPTIONS = "strictly avoid interruptions"
CONFIG_DEFAULT_CONFIG = {CONFIG_SYNC_TIMEOUT: 1, CONFIG_IDLE_SYNC_TIMEOUT: 10, CONFIG_CONFIG_VERSION: 1, CONFIG_STRICTLY_AVOID_INTERRUPTIONS: True}

# Layout

AUTO_SYNC_ICON = QApplication.instance().style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
