"""

Todo:
   - hook on after sync

"""
import sip

from aqt import *
from aqt import gui_hooks
from aqt import QDialog
from aqt import mw
from aqt.utils import tooltip as qttooltip

from aqt.qt import *
from aqt.about import ClosableQDialog
from aqt.addons import AddonsDialog
from aqt.browser import Browser
from aqt.stats import NewDeckStats
from aqt.progress import ProgressDialog
from aqt.addcards import AddCards


production = False
# production parameters
REINSTALL_EVENT_LISTENER_TIMEOUT = 0.5 * 1000 * 60
SYNC_TIMEOUT = REINSTALL_EVENT_LISTENER_TIMEOUT + 0.5 * 1000 * 60
SYNC_TIMEOUT_NO_ACTIVITY = 5 * 1000 * 60

if not production:
    # testing parameters
    REINSTALL_EVENT_LISTENER_TIMEOUT = 0.1 * 1000 * 60
    SYNC_TIMEOUT = REINSTALL_EVENT_LISTENER_TIMEOUT + 0.1 * 1000 * 60
    SYNC_TIMEOUT_NO_ACTIVITY = 5 * 1000 * 60

LEGAL_STATES = ["deckBrowser"]
timer = None
open_windows = []
main_class = None

def tooltip(message):
    if not production:
        qttooltip(message)


class CloseEventListener(QDialog):
    def __init__(self, monitor):
        super(CloseEventListener, self).__init__()
        self.monitor = monitor

    def eventFilter(self, obj: QObject, evt: QEvent):
        event_id = evt.type()
        if event_id in [19]:
            self.monitor.child_removed(obj)
        return False


class AddChildEventListener(QDialog):
    def __init__(self, main_class):
        super(AddChildEventListener, self).__init__()
        self.main_class = main_class

    def eventFilter(self, obj: QObject, evt: QEvent):
        event_id = evt.type()

        if event_id in [68]:
            good_classes = [Browser, ClosableQDialog, QMainWindow, NewDeckStats, AddCards, AddonsDialog]
            if isinstance(obj, QMessageBox) or isinstance(obj, ProgressDialog) or isinstance(obj, AnkiQt):
                return False
            if isinstance(obj, QDialog) or isinstance(obj, QMainWindow):
                self.main_class.new_child(obj)

        return False


class OpenWindowMonitor:

    def __init__(self, mw):
        self.children = []
        self.close_event_listener = CloseEventListener(self)
        self.add_child_event_listener = AddChildEventListener(self)
        self.mw = mw
        self.mw.app.installEventFilter(self.add_child_event_listener)

    def can_unwrap(self, obj):
        try:
            sip.unwrapinstance(obj)
            return True
        except RuntimeError:
            return False

    def check_children(self):
        for child in self.children:
            if not self.can_unwrap(child):
                self.children.remove(child)

    def new_child(self, obj):
        if obj not in self.children:
            self.children.append(obj)

    def child_removed(self, obj):
        if obj in self.children:
            self.children.remove(obj)

    def has_open_windows(self):
        self.check_children()
        return len(self.children) > 0


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
        self.event_listener = UserActivityEventListener(self)
        self.activity_since_sync = True
        self.open_window_monitor = OpenWindowMonitor(mw)
        self.install_event_listener()

    def start_install_event_listener_timer(self):
        if self.reinstall_event_listener_timer is not None:
            self.reinstall_event_listener_timer.stop()
        self.reinstall_event_listener_timer = mw.progress.timer(REINSTALL_EVENT_LISTENER_TIMEOUT, self.install_event_listener, False)

    def is_bad_state(self):
        if self.open_window_monitor.has_open_windows():
            return True
        if mw.web.hasFocus() or mw.toolbarWeb.hasFocus() or mw.bottomWeb.hasFocus():
            return True
        if mw.state not in LEGAL_STATES:
            return True

    def install_event_listener(self):
        bad_state = self.is_bad_state()
        if bad_state:
            tooltip("bad state")
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
        mw.onSync()  # pass "reactivate sync timer" to after sync so it pauses if theres a problem with finishing the sync
        self.activity_since_sync = False
        self.start_sync_timer()

    def start_sync_timer(self):
        if self.sync_timer is not None:
            self.sync_timer.stop()
        if self.activity_since_sync:
            self.sync_timer = mw.progress.timer(SYNC_TIMEOUT, self.do_sync, False)
        else:
            self.sync_timer = mw.progress.timer(SYNC_TIMEOUT_NO_ACTIVITY, self.do_sync, False)


def init():
    global main_class
    main_class = SyncRoutine()


gui_hooks.main_window_did_init.append(lambda *args: init())

