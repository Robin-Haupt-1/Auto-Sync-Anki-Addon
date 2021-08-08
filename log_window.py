from aqt.qt import *
from PyQt5 import QtCore, QtGui
from aqt.utils import showInfo
from .constants import AUTO_SYNC_ICON

class LogManager:
    def __init__(self):
        self.log = ""

        self.log_dialog = None

    def write(self, line: str):
        self.log += line + "\n"
        if self.log_dialog:
            self.log_dialog.refresh_log()

    def read(self):
        return self.log

    def listen(self, log_dialog):
        self.log_dialog = log_dialog


class AutoSyncLogDialog(QDialog):
    def __init__(self, log_manager: LogManager, parent):
        super(AutoSyncLogDialog, self).__init__()
        self.log_manager = log_manager
        self.parent=parent

        # set up UI

        self.setWindowIcon(AUTO_SYNC_ICON)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.NoWrap)

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.log_output, 0, 0)

        self.setLayout(grid)

        self.setWindowTitle('Auto Sync Log')
        self.setMinimumWidth(750)
        self.refresh_log()
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.log_manager.listen(self)

    def refresh_log(self):
        self.log_output.setText(self.log_manager.read())
        sb = self.log_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.parent.on_log_dialog_close()

