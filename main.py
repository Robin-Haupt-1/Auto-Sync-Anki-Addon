from aqt import gui_hooks, mw
from aqt.qt import QAction
from .config import AutoSyncConfigManager
from .options_dialog import on_options_call
from .sync_routine import SyncRoutine
from .log_window import *

sync_routine = None
config_manager = None
log_manager = None


def init():
    # declare variables as global so they won't be garbage collected
    global sync_routine, config_manager, log_manager

    # set up config manager, log manager and sync routine
    log_manager = LogManager()
    config_manager = AutoSyncConfigManager(mw)
    sync_routine = SyncRoutine(config_manager, log_manager)

    # listen to sync activity
    gui_hooks.sync_will_start.append(sync_routine.sync_initiated)
    gui_hooks.sync_did_finish.append(sync_routine.sync_finished)

    # add options entry to Anki menu
    options_action = QAction("Auto Sync Options ...", mw)
    options_action.triggered.connect(lambda _, o=mw: on_options_call(config_manager, sync_routine, log_manager))
    mw.form.menuTools.addAction(options_action)
    gui_hooks.profile_will_close.append(lambda *args: mw.form.menuTools.removeAction(options_action))


gui_hooks.profile_did_open.append(lambda *args: init())
