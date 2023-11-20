from aqt.qt import QDialog, QGridLayout, QTextEdit
from PyQt6.QtGui import QCloseEvent
from .constants import AUTO_SYNC_ICON


class LogManager:
    def __init__(self):
        self.log = ""
        self.log_dialog = None

    def write(self, line: str):
        """Add a single line to the log"""
        self.log += line + "\n"
        # call the log dialog window to refresh it
        if self.log_dialog:
            self.log_dialog.refresh_log()

    def read(self):
        """Get all log entries seperated by \\n"""
        return self.log

    def register(self, log_dialog):
        """Register AutoSyncLogDialog instance to listen to log output"""
        self.log_dialog = log_dialog


class AutoSyncLogDialog(QDialog):
    def __init__(self, log_manager: LogManager, parent):
        super(AutoSyncLogDialog, self).__init__()
        self.log_manager = log_manager
        self.parent = parent

        # set up log TextEdit
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        # Window layout
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(self.log_output, 0, 0)

        self.setLayout(grid)
        self.setWindowTitle('Auto Sync Log')
        self.setWindowIcon(AUTO_SYNC_ICON)
        self.setMinimumWidth(750)
        self.refresh_log()

        # listen to the log output
        self.log_manager.register(self)

    def refresh_log(self):
        """Refresh the log and scroll the TextEdit to the bottom"""
        self.log_output.setText(self.log_manager.read())
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.parent.on_log_dialog_close()
