"""
Todo:
    - QApplication::topLevelWidgets() to get list of top level widgets
"""

from aqt.utils import showInfo, tooltip
from aqt import *
from aqt import gui_hooks
import sip
from .constants import event_types
from datetime import datetime

deck_browser = None


def is_deleted(obj):
    try:
        sip.unwrapinstance(obj)
    except RuntimeError:
        return True
    return False


def isEditorVisible():
    widget_deleted = is_deleted(editor.widget)
    showInfo(str(widget_deleted))
    if widget_deleted:
        timer.stop()


def onEditorlaunch(e):
    global editor
    editor = e
    showInfo(str(e.widget))
    global timer
    timer = mw.progress.timer(1000 * 5, isEditorVisible, True)


class MyFilter(QDialog):
    def __init__(self, mw):
        super(MyFilter, self).__init__()

    def eventFilter(self, obj: QObject, evt: QEvent):
        event_id = evt.type()
        if event_id in [2, 6]:
            tooltip(event_types[evt.type()])
            return False
        return False


filter = MyFilter(mw)


def deck_browser_rendered(browser):
    global deck_browser
    deck_browser = browser


def init():
    mw.app.installEventFilter(filter)


d = MyFilter(mw)

gui_hooks.deck_browser_did_render.append(lambda *args: deck_browser_rendered(*args))
gui_hooks.main_window_did_init.append(lambda *args: init())
# DeckBrowser.installEventFilter(d)
# mw.eventFilter()
# gui_hooks.editor_did_init.append(lambda args: onEditorlaunch(args))


# timer = mw.progress.timer(1000 * 6, alert, False)
