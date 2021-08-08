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
    def __init__(self, sync_routine):
        super(UserActivityEventListener, self).__init__()
        self.sync_routine = sync_routine

    def eventFilter(self, obj: QObject, evt: QEvent):
        event_id = evt.type()
        if event_id in [2, 5, 6]:  # 2: 'MouseButtonPress', 5: 'MouseMove',  6: 'KeyPress'
            self.sync_routine.on_user_activity()
        return False


class SyncRoutine:
    def __init__(self, config: AutoSyncConfigManager, log_manager: LogManager):
        self.config = config
        self.log_manager = log_manager
        self.countdown_to_sync_timer = None
        self.sync_timer = None
        self.sync_in_progress = False
        self.activity_since_sync = True
        self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT = 0.2 * 1000 * 60  # Reinstall the event listener every 0.2 minutes. If it were running all the time, it would impact performance
        self.SYNC_TIMEOUT_NO_ACTIVITY = (self.config.get(CONFIG_IDLE_SYNC_TIMEOUT) * 1000 * 60) - round(self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT / 2)
        self.SYNC_TIMEOUT = (self.config.get(CONFIG_SYNC_TIMEOUT) * 1000 * 60) - round(self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT / 2)
        self.STRICTLY_AVOID_INTERRUPTIONS = self.config.get(CONFIG_STRICTLY_AVOID_INTERRUPTIONS)

        self.user_activity_event_listener = UserActivityEventListener(self)
        self.start_countdown_to_sync_timer()

    def _log(self, message):
        self.log_manager.write(f"[{datetime.datetime.now().strftime('%H-%M-%S')}]: {message}")
        if log_to_stdout:
            print(f"[Auto Sync] {datetime.datetime.now().strftime('%H-%M-%S')}: {message}")

    def start_countdown_to_sync_timer(self):
        """After a few seconds, start the timer and install the event listener"""
        if self.countdown_to_sync_timer is not None:
            self.countdown_to_sync_timer.stop()
        self._log(f"Waiting {self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT / 60000} minutes to start sync timer")
        self.countdown_to_sync_timer = mw.progress.timer(self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT, self.start_sync_timer, False)

    def is_bad_state(self):
        """Check if the app is in any state that it shouldn't automatically sync in to avoid interrupting the user's activity"""
        reasons = []
        if self.sync_in_progress:
            reasons.append("Sync in progress")
        if self.STRICTLY_AVOID_INTERRUPTIONS:
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
            self._log(f"Can't start sync timer ({', '.join(reasons)})")
            return True

    def start_sync_timer(self):
        """Start the background timer to automatically sync the collection and install an event filter to stop it at any user activity"""
        if self.is_bad_state():
            self.start_countdown_to_sync_timer()
        else:
            self._log(f"Started sync timer, waiting for {(self.SYNC_TIMEOUT if self.activity_since_sync else self.SYNC_TIMEOUT_NO_ACTIVITY) / 60000} minutes")
            mw.app.installEventFilter(self.user_activity_event_listener)
            if self.sync_timer is not None:
                self.sync_timer.stop()
            self.sync_timer = mw.progress.timer(self.SYNC_TIMEOUT if self.activity_since_sync else self.SYNC_TIMEOUT_NO_ACTIVITY, self.do_sync, False)

    def stop_sync_timer(self):
        """Stop the background timer to automatically sync the collection and remove the event filter that checks for user activity"""

        mw.app.removeEventFilter(self.user_activity_event_listener)
        if self.sync_timer is not None:
            self.sync_timer.stop()
        self.start_countdown_to_sync_timer()

    def on_user_activity(self):
        self._log("User activity! Stopped sync timer")
        self.activity_since_sync = True
        self.stop_sync_timer()

    def do_sync(self):
        """Force the app to sync the collection if there's an internet connection"""
        if not has_internet_connection():
            self._log(f"No internet connection, delaying sync for {self.SYNC_TIMEOUT / 60000} minutes")
            self.activity_since_sync = True  # shorten duration to next sync
            self.start_sync_timer()
            return
        mw.app.removeEventFilter(self.user_activity_event_listener)
        self._log("Syncing")
        self.sync_in_progress = True
        mw.onSync()

    def sync_finished(self, *args):
        """When one sync cycle has finished, start the whole process over"""
        self._log("Sync completed")
        self.sync_in_progress = False
        self.activity_since_sync = False
        self.start_countdown_to_sync_timer()

    def sync_initiated(self, *args):
        """Corner case: user initiates sync but it can't finish. Set this parameter to avoid starting another failed sync attempt on top"""
        if not log_to_stdout:
            self._log("Sync initiated")
        self.sync_in_progress = True

    def load_config(self):
        self.SYNC_TIMEOUT_NO_ACTIVITY = (self.config.get(CONFIG_IDLE_SYNC_TIMEOUT) * 1000 * 60) - round(self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT / 2)
        self.SYNC_TIMEOUT = (self.config.get(CONFIG_SYNC_TIMEOUT) * 1000 * 60) - round(self.COUNTDOWN_TO_SYNC_TIMER_TIMEOUT / 2)
        self.STRICTLY_AVOID_INTERRUPTIONS = (self.config.get(CONFIG_STRICTLY_AVOID_INTERRUPTIONS))

        self._log(f"Loaded config. New sync / idle sync timeout: {self.SYNC_TIMEOUT / 60000} minutes, {self.SYNC_TIMEOUT_NO_ACTIVITY / 60000} minutes. Strictly avoid interruptions: {'on' if self.STRICTLY_AVOID_INTERRUPTIONS else 'off'}")

    def reload_config(self):
        self.stop_sync_timer()
        self.load_config()
        self.start_countdown_to_sync_timer()
