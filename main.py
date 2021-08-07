from aqt import gui_hooks
from aqt import mw
from aqt.qt import *
# addon imports
from .config import AutoSyncConfigManager
from .options_dialog import onOptionsCall
from .sync_routine import SyncRoutine


def init():
    global sync_routine, config
    # mw.col.conf.remove(AUTO_SYNC_CONFIG_NAME)
    config = AutoSyncConfigManager(mw)
    config.reset_config()
    sync_routine = SyncRoutine(config)
    gui_hooks.sync_did_finish.append(sync_routine.sync_finished)

    options_action = QAction("Auto Sync Options ...", mw)
    options_action.triggered.connect(lambda _, o=mw: onOptionsCall(config, sync_routine))
    mw.form.menuTools.addAction(options_action)


sync_routine = None
config = None
gui_hooks.profile_did_open.append(lambda *args: init())
