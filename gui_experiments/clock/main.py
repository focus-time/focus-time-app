import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlDebuggingEnabler
from PySide6.QtCore import QTimer, QObject, Signal

from time import localtime

app = QGuiApplication(sys.argv)

engine = QQmlApplicationEngine()
engine.quit.connect(app.quit)
engine.load('main.qml')


class Backend(QObject):

    hms = Signal(int, int, int, arguments=['hours','minutes','seconds'])

    def __init__(self):
        super().__init__()

        # Define timer.
        self.timer = QTimer()
        self.timer.setInterval(100)  # msecs 100 = 1/10th sec
        self.timer.timeout.connect(self.update_time)
        self.timer.start()

    def update_time(self):
        # Pass the current time to QML.
        local_time = localtime()
        self.hms.emit(local_time.tm_hour, local_time.tm_min, local_time.tm_sec)


# Define our backend object, which we pass to QML.
backend = Backend()

engine.rootObjects()[0].setProperty('backend', backend)

# Initial call to trigger first update. Must be after the setProperty to connect signals.
backend.update_time()

sys.exit(app.exec())

QQmlDebuggingEnabler.enableDebugging(True)
