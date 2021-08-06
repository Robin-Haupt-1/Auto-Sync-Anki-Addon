from aqt import gui_hooks
from aqt import mw
from aqt.utils import tooltip as qttooltip
from aqt.qt import *
from aqt import dialogs as aqt_dialogs
import socket

sync_routine = None

production = False
# production parameters
REINSTALL_EVENT_LISTENER_TIMEOUT = 0.5 * 1000 * 60
SYNC_TIMEOUT = REINSTALL_EVENT_LISTENER_TIMEOUT + 0.5 * 1000 * 60
SYNC_TIMEOUT_NO_ACTIVITY = 5 * 1000 * 60

if not production: # development parameters
    REINSTALL_EVENT_LISTENER_TIMEOUT = 0.1 * 1000 * 60
    SYNC_TIMEOUT = REINSTALL_EVENT_LISTENER_TIMEOUT + 0.1 * 1000 * 60
    SYNC_TIMEOUT_NO_ACTIVITY = 0.1 * 1000 * 60


def tooltip(message):
    if not production:
        qttooltip(message)


class UserActivityEventListener(QDialog):
    def __init__(self, sync_routine):
        super(UserActivityEventListener, self).__init__()
        self.sync_routine = sync_routine

    def eventFilter(self, obj: QObject, evt: QEvent):
        event_id = evt.type()
        if event_id in [2, 6, 5]:
            self.sync_routine.on_user_activity()
        return False


class SyncRoutine:
    def __init__(self):
        self.reinstall_event_listener_timer = None
        self.sync_timer = None
        self.sync_in_progress = False
        self.activity_since_sync = True
        self.event_listener = UserActivityEventListener(self)

        self.install_event_listener_and_sync_timer()

    def start_install_event_listener_timer(self):
        if self.reinstall_event_listener_timer is not None:
            self.reinstall_event_listener_timer.stop()
        self.reinstall_event_listener_timer = mw.progress.timer(REINSTALL_EVENT_LISTENER_TIMEOUT, self.install_event_listener_and_sync_timer, False)

    def is_bad_state(self):
        reasons = []
        if not self.has_internet_connection():
            reasons.append("No internet")
        if self.sync_in_progress:
            reasons.append("Sync in progress")
        if not aqt_dialogs.allClosed():
            reasons.append("Windows open")
        if mw.web.hasFocus() or mw.toolbarWeb.hasFocus() or mw.bottomWeb.hasFocus():
            reasons.append("Main Window has focus")
        if mw.state != "deckBrowser":
            reasons.append("Main Window in bad state (" + mw.state + ")")
        if len(reasons) > 0:
            tooltip("bad state. reasons: " + ", ".join(reasons))
            return True

    def install_event_listener_and_sync_timer(self):
        if self.is_bad_state():
            self.start_install_event_listener_timer()
        else:
            tooltip("installed event listener")
            mw.app.installEventFilter(self.event_listener)
            self.start_sync_timer()

    def remove_event_listener(self):
        tooltip("removed event listener")
        mw.app.removeEventFilter(self.event_listener)
        self.sync_timer.stop()
        self.start_install_event_listener_timer()

    def on_user_activity(self):
        self.activity_since_sync = True
        self.remove_event_listener()

    def do_sync(self):
        tooltip("Syncing")
        self.sync_in_progress = True
        mw.onSync()

    def sync_finished(self, *args):
        self.sync_in_progress = False
        tooltip("sync finished")
        self.activity_since_sync = False
        self.start_install_event_listener_timer()

    def start_sync_timer(self):
        if self.sync_timer is not None:
            self.sync_timer.stop()
        self.sync_timer = mw.progress.timer(SYNC_TIMEOUT if self.activity_since_sync else SYNC_TIMEOUT_NO_ACTIVITY, self.do_sync, False)

    def has_internet_connection(self, host="8.8.8.8", port=53, timeout=3):
        """Try connecting to the Google DNS server to check internet connectivity"""
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            return False


def init():
    global sync_routine
    sync_routine = SyncRoutine()
    gui_hooks.sync_did_finish.append(sync_routine.sync_finished)


gui_hooks.main_window_did_init.append(lambda *args: init())
