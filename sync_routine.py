import datetime
from aqt import dialogs as aqt_dialogs
from aqt import mw
from aqt.qt import QDialog, QObject, QEvent
from .config import AutoSyncConfigManager
from .utils import has_internet_connection
from .constants import *
from .log_window import LogManager

log_to_stdout = False


class UserActivityEventListener(QDialog):
    """If the user moves the mouse or presses a key within any Anki window, call the sync routine"""

    def __init__(self, sync_routine):
        super(UserActivityEventListener, self).__init__()
        self.sync_routine = sync_routine

    def eventFilter(self, obj: QObject, evt: QEvent):
        if evt.type() in [2, 5, 6]:  # 2: 'MouseButtonPress', 5: 'MouseMove',  6: 'KeyPress'
            self.sync_routine.on_user_activity()
        # if this returns true, the event won't be propagated further
        return False


class SyncRoutine:
    def __init__(self, config: AutoSyncConfigManager, log_manager: LogManager):
        self.config = config
        self.log_manager = log_manager

        # initiate instance attributes
        self.countdown_to_sync_timer: mw.progress.timer = None
        self.sync_timer: mw.progress.timer = None
        self.sync_in_progress: bool = False
        self.activity_since_sync: bool = True
        self.user_activity_event_listener = UserActivityEventListener(self)

        # set constants (load from config)
        self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT = 0.2 * 1000 * 60  # Reinstall the event listener every 0.2 minutes. If it were running all the time, it would impact performance
        self.SYNC_TIMEOUT_NO_ACTIVITY: int = None
        self.SYNC_TIMEOUT: int = None
        self.STRICTLY_AVOID_INTERRUPTIONS: int = None
        self.load_config()

        # start auto sync process
        self.start_countdown_to_sync_timer()

    def log(self, message):
        """Write message to log window and optionally stdout"""
        self.log_manager.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}")
        if log_to_stdout:
            print(f"[Auto Sync] {datetime.datetime.now().strftime('%H:%M:%S')} {message}")

    def start_countdown_to_sync_timer(self):
        """Start timer that after a few seconds starts the sync timer and installs the event listener"""
        if self.countdown_to_sync_timer is not None:
            self.countdown_to_sync_timer.stop()
        self.log(f"Waiting {self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT / 60000} minutes to start sync timer")
        self.countdown_to_sync_timer = mw.progress.timer(self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT, self.start_sync_timer, False)

    def is_good_state(self):
        """Check that the app isn't in any state that it shouldn't automatically sync in to avoid interrupting the user's activity"""
        reasons = []  # all the reasons why it can't sync now will be collected in this
        if self.sync_in_progress:
            reasons.append("Sync in progress")
        if self.STRICTLY_AVOID_INTERRUPTIONS:
            # check if any dialogs are open
            if not aqt_dialogs.allClosed():
                try:
                    open_windows = [x[0] for x in aqt_dialogs._dialogs.items() if x[1][1]]
                    reasons.append(f"Windows are open: {', '.join(open_windows)}")
                except:
                    reasons.append(f"Windows are open")
            if mw.web.hasFocus() or mw.toolbarWeb.hasFocus() or mw.bottomWeb.hasFocus():
                reasons.append("Main Window has focus")
            if mw.state not in ["deckBrowser", "overview"]:
                reasons.append("Main Window is not on deck browser or overview screen (state: " + mw.state + ")")

        if len(reasons) > 0:
            self.log(f"Can't start sync timer ({', '.join(reasons)})")
            return False
        return True

    def start_sync_timer(self):
        """Start the background timer to automatically sync the collection and install an event filter to stop it at any user activity"""
        if self.is_good_state():
            self.log(f"Started sync timer, waiting for {(self.SYNC_TIMEOUT if self.activity_since_sync else self.SYNC_TIMEOUT_NO_ACTIVITY) / 60000} minutes")
            mw.app.installEventFilter(self.user_activity_event_listener)
            # stop any old sync_timer timers and start a new one
            if self.sync_timer is not None:
                self.sync_timer.stop()
            self.sync_timer = mw.progress.timer(self.SYNC_TIMEOUT if self.activity_since_sync else self.SYNC_TIMEOUT_NO_ACTIVITY, self.do_sync, False)
        else:
            # try again in a few seconds
            self.start_countdown_to_sync_timer()

    def stop_sync_timer(self):
        """Stop the background timer to automatically sync the collection and remove the event filter that checks for user activity.
        Start timer to start it again"""
        mw.app.removeEventFilter(self.user_activity_event_listener)
        if self.sync_timer is not None:
            self.sync_timer.stop()
        self.start_countdown_to_sync_timer()

    def on_user_activity(self):
        """Stop sync timer and register user activity (shortens timeout till next sync)"""
        self.log("User activity! Stopped sync timer")
        self.activity_since_sync = True
        self.stop_sync_timer()

    def do_sync(self):
        """Force the app to sync the collection if there's an internet connection"""
        if not has_internet_connection():
            self.log(f"No internet connection, delaying sync for {self.SYNC_TIMEOUT / 60000} minutes")
            self.activity_since_sync = True  # shorten duration to next sync
            self.start_sync_timer()
            return
        mw.app.removeEventFilter(self.user_activity_event_listener)
        self.log("Syncing")
        self.sync_in_progress = True
        mw.onSync()

    def sync_finished(self, *args):
        """When one sync cycle has finished, start the whole process over"""
        self.log("Sync completed")
        self.sync_in_progress = False
        self.activity_since_sync = False
        self.start_countdown_to_sync_timer()

    def sync_initiated(self, *args):
        """Corner case: user initiates sync but it can't finish. Set this parameter to avoid starting another failed sync attempt on top"""
        self.log("Sync initiated")
        self.sync_in_progress = True

    def load_config(self):
        self.SYNC_TIMEOUT_NO_ACTIVITY = (self.config.get(CONFIG_IDLE_SYNC_TIMEOUT) * 1000 * 60) - round(self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT / 2)
        self.SYNC_TIMEOUT = (self.config.get(CONFIG_SYNC_TIMEOUT) * 1000 * 60) - round(self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT / 2)
        self.STRICTLY_AVOID_INTERRUPTIONS = (self.config.get(CONFIG_STRICTLY_AVOID_INTERRUPTIONS))

        self.log(f"Loaded config. New sync / idle sync timeout: {self.SYNC_TIMEOUT / 60000} minutes, {self.SYNC_TIMEOUT_NO_ACTIVITY / 60000} minutes. Strictly avoid interruptions: {'on' if self.STRICTLY_AVOID_INTERRUPTIONS else 'off'}")

    def reload_config(self):
        """reload the config and restart the sync timer timeout"""
        self.load_config()
        self.stop_sync_timer()
