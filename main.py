from aqt import gui_hooks
from aqt import mw
from aqt.utils import tooltip as qttooltip
from aqt.qt import *
from aqt import dialogs as aqt_dialogs
from ._classes import *


from .utils import has_internet_connection

production = False

# production parameters
COUNTDOWN_TO_SYNC_TIMER_TIMEOUT = 0.5 * 1000 * 60
SYNC_TIMEOUT = COUNTDOWN_TO_SYNC_TIMER_TIMEOUT + 0.5 * 1000 * 60
SYNC_TIMEOUT_NO_ACTIVITY = 5 * 1000 * 60

if not production:  # development parameters
    COUNTDOWN_TO_SYNC_TIMER_TIMEOUT = 0.1 * 1000 * 60
    SYNC_TIMEOUT = 0.1 * 1000 * 60
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
        if event_id in [2, 5, 6]:  # 2: 'MouseButtonPress', 5: 'MouseMove',  6: 'KeyPress'
            self.sync_routine.on_user_activity()
        return False


class SyncRoutine:
    def __init__(self):
        self.countdown_to_sync_timer = None
        self.sync_timer = None
        self.sync_in_progress = False
        self.activity_since_sync = True
        self.user_activity_event_listener = UserActivityEventListener(self)
        self.start_countdown_to_sync_timer()

    def start_countdown_to_sync_timer(self):
        """After a few seconds, start the timer and install the event listener"""
        if self.countdown_to_sync_timer is not None:
            self.countdown_to_sync_timer.stop()
        self.countdown_to_sync_timer = mw.progress.timer(COUNTDOWN_TO_SYNC_TIMER_TIMEOUT, self.start_sync_timer, False)

    def is_bad_state(self):
        """Check if the app is in any state that it shouldn't automatically sync in to avoid disturbing the user"""
        reasons = []
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

    def start_sync_timer(self):
        """Start the background timer to automatically sync the collection and install an event filter to stop it at any user activity"""
        if self.is_bad_state():
            self.start_countdown_to_sync_timer()
        else:
            tooltip("installed event listener")
            mw.app.installEventFilter(self.user_activity_event_listener)
            if self.sync_timer is not None:
                self.sync_timer.stop()
            self.sync_timer = mw.progress.timer(SYNC_TIMEOUT if self.activity_since_sync else SYNC_TIMEOUT_NO_ACTIVITY, self.do_sync, False)

    def stop_sync_timer(self):
        """Stop the background timer to automatically sync the collection and remove the event filter that checks for user activity"""
        tooltip("removed event listener")
        mw.app.removeEventFilter(self.user_activity_event_listener)
        if self.sync_timer is not None:
            self.sync_timer.stop()
        self.start_countdown_to_sync_timer()

    def on_user_activity(self):
        self.activity_since_sync = True
        self.stop_sync_timer()

    def do_sync(self):
        """Force the app to sync the collection if there's an internet connection"""
        if not has_internet_connection():
            tooltip("delaying sync, no internet connection")
            self.activity_since_sync = True  # shorten duration to next sync
            self.start_sync_timer()
            return
        mw.app.removeEventFilter(self.user_activity_event_listener)
        tooltip("Syncing")
        self.sync_in_progress = True
        mw.onSync()

    def sync_finished(self, *args):
        """When one sync cycle has finished, start the whole process over"""
        tooltip("sync finished")
        self.sync_in_progress = False
        self.activity_since_sync = False
        self.start_countdown_to_sync_timer()


def init():
    global sync_routine
    sync_routine = SyncRoutine()
    gui_hooks.sync_did_finish.append(sync_routine.sync_finished)


sync_routine = None
gui_hooks.main_window_did_init.append(lambda *args: init())
