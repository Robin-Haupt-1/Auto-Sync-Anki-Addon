from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from aqt.qt import QDialog, QSpinBox, QLabel, QCheckBox, QGridLayout, QPushButton
from .sync_routine import SyncRoutine
from .config import AutoSyncConfigManager
from .constants import *
from .log_window import AutoSyncLogDialog, LogManager


class AutoSyncOptionsDialog(QDialog):
    def __init__(self, config: AutoSyncConfigManager, sync_routine: SyncRoutine, log_manager: LogManager):
        super(AutoSyncOptionsDialog, self).__init__()
        self.config = config
        self.sync_routine: SyncRoutine = sync_routine
        self.log_manager = log_manager

        self.log_dialog_instance = None

        # set up UI elements
        self.sync_timeout_spinbox = QSpinBox()
        self.idle_sync_timeout_spinbox = QSpinBox()
        self.sync_on_open_windows_checkbox = QCheckBox()

        self.setup_ui()

    def change_sync_timeout(self, value):
        if value == 1:
            self.sync_timeout_spinbox.setSuffix(" minute")
        else:
            self.sync_timeout_spinbox.setSuffix(" minutes")
        self.config.set(CONFIG_SYNC_TIMEOUT, value)
        self.sync_routine.reload_config()

    def change_idle_sync_timeout(self, f):
        if f == 1:
            self.idle_sync_timeout_spinbox.setSuffix(" minute")
        else:
            self.idle_sync_timeout_spinbox.setSuffix(" minutes")
        self.config.set(CONFIG_IDLE_SYNC_TIMEOUT, f)
        self.sync_routine.reload_config()

    def change_strictly_avoid_interruption(self, enabled):

        self.config.set(CONFIG_STRICTLY_AVOID_INTERRUPTIONS, enabled)
        self.sync_routine.reload_config()

    def change_strict_background_mode_label_click(self, enabled):
        self.config.set(CONFIG_STRICTLY_AVOID_INTERRUPTIONS, enabled)
        self.sync_routine.reload_config()

    def setup_ui(self):
        self.setWindowTitle('Auto Sync Options')
        self.setWindowIcon(AUTO_SYNC_ICON)
        self.setMaximumWidth(500)
        self.setMaximumHeight(150)

        # "Sync after" option

        sync_timeout_label = QLabel('Sync after')
        sync_timeout_label.setToolTip('How many minutes after you have last interacted with Anki the program will wait to start the sync')
        self.sync_timeout_spinbox.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter)
        #self.sync_timeout_spinbox.setFixedWidth(110)
        self.sync_timeout_spinbox.setMinimum(1)

        self.sync_timeout_spinbox.setValue(self.config.get(CONFIG_SYNC_TIMEOUT))
        if self.sync_timeout_spinbox.value() == 1:
            self.sync_timeout_spinbox.setSuffix(" minute")
        else:
            self.sync_timeout_spinbox.setSuffix(" minutes")
        self.sync_timeout_spinbox.setToolTip('How many minutes after you have last interacted with Anki the program will wait to start the sync')
        self.sync_timeout_spinbox.valueChanged.connect(self.change_sync_timeout)

        # "Idle Sync after" option

        idle_sync_timeout_label = QLabel('When the program is idle, sync every')
        idle_sync_timeout_label.setToolTip('While you are not using Anki, the program will keep syncing in the background (in case you are using Anki on mobile or web and there are changes to sync)')
        self.idle_sync_timeout_spinbox.setMinimum(1)
        self.idle_sync_timeout_spinbox.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTrailing | Qt.AlignmentFlag.AlignVCenter)
        #self.idle_sync_timeout_spinbox.setFixedWidth(110)
        self.idle_sync_timeout_spinbox.setValue(self.config.get(CONFIG_IDLE_SYNC_TIMEOUT))
        if self.idle_sync_timeout_spinbox.value() == 1:
            self.idle_sync_timeout_spinbox.setSuffix(" minute")
        else:
            self.idle_sync_timeout_spinbox.setSuffix(" minutes")
        self.idle_sync_timeout_spinbox.setToolTip('While you are not using Anki, the program will keep syncing in the background (in case you are using Anki on mobile or web and there are changes to sync)')
        self.idle_sync_timeout_spinbox.valueChanged.connect(self.change_idle_sync_timeout)

        # "Strictly avoid interruptions"" checkbox

        strictly_avoid_interruptions_label = QLabel("Strictly avoid interruptions (recommended)")
        strictly_avoid_interruptions_label.setToolTip("Will not auto sync if cards are being reviewed, the card browser or similar windows are open <br>or the main window has focus (isn't minimized or in the background)")
        strictly_avoid_interruptions_checkbox = QCheckBox()
        strictly_avoid_interruptions_checkbox.setToolTip("Will not auto sync if cards are being reviewed, the card browser or similar windows are open <br>or the main window has focus (isn't minimized or in the background)")
        strictly_avoid_interruptions_checkbox.setChecked(self.config.get(CONFIG_STRICTLY_AVOID_INTERRUPTIONS))
        strictly_avoid_interruptions_checkbox.stateChanged.connect(self.change_strictly_avoid_interruption)
        strictly_avoid_interruptions_label.mouseReleaseEvent = lambda *args: strictly_avoid_interruptions_checkbox.toggle()

        # Show log button
        open_log_button = QPushButton()

        open_log_button.setText("Show log ...")
        open_log_button.clicked.connect(lambda *args: self.on_log_dialog_call())
        open_log_button.setMaximumWidth(100)

        # Close button

        close_button = QPushButton()
        close_button.setText("Close")
        close_button.clicked.connect(lambda *args: self.close())

        # Set up layout

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(sync_timeout_label, 0, 0)
        grid.addWidget(self.sync_timeout_spinbox, 0, 1)

        grid.addWidget(idle_sync_timeout_label, 1, 0)
        grid.addWidget(self.idle_sync_timeout_spinbox, 1, 1)
        grid.addWidget(strictly_avoid_interruptions_label, 3, 0)
        grid.addWidget(strictly_avoid_interruptions_checkbox, 3, 1)

        grid.addWidget(open_log_button, 5, 0)
        grid.addWidget(close_button, 5, 1)

        self.setLayout(grid)

    def on_log_dialog_call(self):
        """Bring the log window to the foreground if one is open, else open a new one """
        if self.log_dialog_instance:
            self.log_dialog_instance.raise_()
            return
        dialog = AutoSyncLogDialog(self.log_manager, self)
        self.log_dialog_instance = dialog
        dialog.show()
        dialog.exec()

    def on_log_dialog_close(self):
        self.log_dialog_instance = None

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.log_dialog_instance:
            self.log_dialog_instance.close()


def on_options_call(conf, sync_routine, log_manager):
    """Open settings dialog"""
    dialog = AutoSyncOptionsDialog(conf, sync_routine, log_manager)
    dialog.show()
    dialog.exec()
