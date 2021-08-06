from aqt import *

from aqt.qt import *
from aqt.about import ClosableQDialog
from aqt.addons import AddonsDialog
from aqt.browser import Browser
from aqt.stats import NewDeckStats
from aqt.progress import ProgressDialog
from aqt.addcards import AddCards


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
        if len(self.children) > 0:
            return self.children


class UserActivityEventListener(QDialog):
    def __init__(self, sync_routine):
        super(UserActivityEventListener, self).__init__()
        self.sync_routine = sync_routine

    def eventFilter(self, obj: QObject, evt: QEvent):
        event_id = evt.type()
        if event_id in [2, 6, 5]:
            self.sync_routine.on_user_activity()
        return False

