from aqt.qt import *
from PyQt5 import QtCore
from aqt.utils import showInfo
from aqt import QCoreApplication
from .sync_routine import SyncRoutine
from .config import AutoSyncConfigManager
from .constants import *
from aqt import mw


class AutoSyncOptionsDialog(QDialog):
    def __init__(self, config: AutoSyncConfigManager, sync_routine: SyncRoutine):
        super(AutoSyncOptionsDialog, self).__init__()
        self.config = config
        self.sync_routine: SyncRoutine = sync_routine

        # set up UI elements
        self.sync_timeout_spinbox = QSpinBox()
        self.idle_sync_timeout_spinbox = QSpinBox()
        self.sync_on_open_windows_checkbox = QCheckBox()

        self.setup_ui()

    def change_sync_timeout(self, f):
        if f == 1:
            self.sync_timeout_spinbox.setSuffix(" minute")
        else:
            self.sync_timeout_spinbox.setSuffix(" minutes")
        self.config.set(CONFIG_SYNC_TIMEOUT, f)
        self.sync_routine.reload_config()

    def change_idle_sync_timeout(self, f):
        if f == 1:
            self.idle_sync_timeout_spinbox.setSuffix(" minute")
        else:
            self.idle_sync_timeout_spinbox.setSuffix(" minutes")
        self.config.set(CONFIG_IDLE_SYNC_TIMEOUT, f)
        self.sync_routine.reload_config()


    def setup_ui(self):
        style = QApplication.instance().style()

        icon = style.standardIcon(QStyle.SP_BrowserReload)
        self.setWindowIcon(icon)

        # "Sync after" option

        sync_timeout_label = QLabel('Sync after')
        sync_timeout_label.setToolTip('The program will wait this many minutes after you have last interacted with Anki to start the sync')
        self.sync_timeout_spinbox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.sync_timeout_spinbox.setFixedWidth(80)
        self.sync_timeout_spinbox.setMinimum(1)

        self.sync_timeout_spinbox.setValue(self.config.get(CONFIG_SYNC_TIMEOUT))
        if self.sync_timeout_spinbox.value() == 1:
            self.sync_timeout_spinbox.setSuffix(" minute")
        else:
            self.sync_timeout_spinbox.setSuffix(" minutes")
        self.sync_timeout_spinbox.setToolTip('The program will wait this many minutes after you have last interacted with Anki to start the sync')
        self.sync_timeout_spinbox.valueChanged.connect(self.change_sync_timeout)

        # "Idle Sync after" option

        idle_sync_timeout_label = QLabel('When the program is idle, sync every')
        idle_sync_timeout_label.setToolTip('While you are not using Anki, the program will keep syncing in the background (in case you are using Anki on mobile or web and there are changes to sync)')
        self.idle_sync_timeout_spinbox.setMinimum(1)
        self.idle_sync_timeout_spinbox.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.idle_sync_timeout_spinbox.setFixedWidth(80)
        self.idle_sync_timeout_spinbox.setValue(self.config.get(CONFIG_IDLE_SYNC_TIMEOUT))
        if self.idle_sync_timeout_spinbox.value() == 1:
            self.idle_sync_timeout_spinbox.setSuffix(" minute")
        else:
            self.idle_sync_timeout_spinbox.setSuffix(" minutes")
        self.idle_sync_timeout_spinbox.setToolTip('While you are not using Anki, the program will keep syncing in the background (in case you are using Anki on mobile or web and there are changes to sync)')
        self.idle_sync_timeout_spinbox.valueChanged.connect(self.change_idle_sync_timeout)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(sync_timeout_label, 0, 0)
        grid.addWidget(self.sync_timeout_spinbox, 0, 1)

        grid.addWidget(idle_sync_timeout_label, 1, 0)
        grid.addWidget(self.idle_sync_timeout_spinbox, 1, 1)
        self.setLayout(grid)

        self.setWindowTitle('Auto Sync Options')


def onOptionsCall(conf, sync_routine):
    """Call settings dialog"""
    dialog = AutoSyncOptionsDialog(conf, sync_routine)
    dialog.exec_()
