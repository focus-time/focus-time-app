# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial

import sys
from pathlib import Path

from PySide6 import QtCore
from PySide6.QtCore import QObject, Slot, Signal, QtMsgType, QUrl
from PySide6.QtGui import QGuiApplication, QWindow, QAction, QIcon
from PySide6.QtQml import QQmlApplicationEngine, QmlElement
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


class GuiHandler(QObject):
    setText = Signal(str, arguments=['text'])

    @Slot()
    def handleButtonClick(self):
        self.setText.emit("Hello from Python!")

    @Slot()
    def handleTextChanged(self):
        print("Text changed!")

    def showWindow(self):
        window.show()


def qt_message_handler(mode, context, message):
    if mode == QtMsgType.QtInfoMsg:
        mode = 'Info'
    elif mode == QtMsgType.QtWarningMsg:
        mode = 'Warning'
    elif mode == QtMsgType.QtCriticalMsg:
        mode = 'critical'
    elif mode == QtMsgType.QtFatalMsg:
        mode = 'fatal'
    else:
        mode = 'Debug'
    print("%s: %s (%s:%d, %s)" % (mode, message, context.file, context.line, context.file))


if __name__ == '__main__':
    QtCore.qInstallMessageHandler(qt_message_handler)  # helps us get warnings and errors from QML
    # app = QGuiApplication(sys.argv)
    app = QApplication(sys.argv)  # QSystemTrayIcon requires QApplication, QGuiApplication does not work
    # w = QQuickWidget()
    # w.setSource(QUrl.fromLocalFile('view.qml'))
    # w.show()

    engine = QQmlApplicationEngine()

    # Get the path of the current directory, and then add the name
    # of the QML file, to load it.
    qml_file = Path(__file__).parent / 'view.qml'
    engine.load(qml_file)

    objs = engine.rootObjects()
    if not objs:
        sys.exit(-1)

    gui_handler = GuiHandler()
    window: QWindow = objs[0]
    text_field: QmlElement = window.findChild(QObject, "nameField")
    text_button: QmlElement = window.findChild(QObject, "setTextButton")
    text_field.textEdited.connect(gui_handler.handleTextChanged)
    text_button.clicked.connect(gui_handler.handleButtonClick)
    gui_handler.setText.connect(lambda text: text_field.setProperty("text", text))

    objs[0].setProperty('guiHandler', gui_handler)

    tray_icon_menu = QMenu()
    show_window_action = QAction("Show window")
    show_window_action.triggered.connect(gui_handler.showWindow)
    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    tray_icon_menu.addAction(show_window_action)
    tray_icon_menu.addAction(quit_action)

    tray_icon = QSystemTrayIcon()
    tray_icon.setContextMenu(tray_icon_menu)
    tray_icon.setIcon(QIcon("test.svg"))
    tray_icon.show()

    app.setQuitOnLastWindowClosed(False)

    sys.exit(app.exec())
