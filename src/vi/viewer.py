#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2021. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
import sys

from PyQt5.QtWidgets import QVBoxLayout, QApplication, QDialog, QTextEdit, QWidget, QMenu, QAction
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtCore import Qt
import logging


class ViewerPopup(QMenu):
    def __init__(self, parent, reload_func):
        """Context-Popup-Menu for viewer.

        :param parent: parent window handler
        """
        super(ViewerPopup, self).__init__(parent)
        self.reload = QAction("reload")
        self.reload.triggered.connect(reload_func)
        self.addAction(self.reload)


class ViewText(QTextEdit):
    """Add custom action to reload the content of the Text-Edit field
    """
    reload = None

    def __init__(self, parent=None):
        super(ViewText, self).__init__(parent=parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.generate_context_menu)

    def add_reload_action(self, func):
        if not self.reload:
            self.reload = QAction("reload text", None)
            self.reload.triggered.connect(func)

    def generate_context_menu(self, location):
        menu = self.createStandardContextMenu(location)
        if self.reload:
            menu.addSeparator()
            menu.addAction(self.reload)
        menu.exec_(self.mapToGlobal(location))


class ViewerDialog(QDialog):
    """create a Popup-Dialog showing content
    """
    content_func = None
    reload = None

    def __init__(self, parent=None, content: str = None, title: str = "View"):
        """
        Standard QDialog to show content in a Text-Editor (read-only)
        :param parent: parent window
        :type parent: Handle
        :param content: optional content to be displayed
        :type content: str
        :param title: optional Title for the Dialog-Box
        :type title: str
        """
        QDialog.__init__(self, parent)
        self.LOGGER = logging.getLogger(__name__)
        self.setBaseSize(400, 600)
        self.setWindowTitle(title)
        self.setLayout(QVBoxLayout())
        self.view_text = ViewText()
        self.layout().addWidget(self.view_text)
        self.LOGGER.debug("activated ViewerDialog %s", title)
        if content:
            self.set_content(content)

    def set_content(self, content: str = None):
        """
        set the content of the Text-Edit
        :param content: the content to be displayed (can be a function)
        :type content: any
        """
        if not content and self.content_func:
            content = self.content_func()
        elif not content:
            content = ""
        self.LOGGER.debug("set content (partial): %s...", content[:30])
        self.view_text.setPlainText(content)

    def set_content_function(self, function):
        self.content_func = function
        self.view_text.add_reload_action(self.set_content)
        self.set_content()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self.content_func:
            context_menu = ViewerPopup(self, self.content_func)
            result = context_menu.exec_(self.mapToGlobal(event.pos()))
            if result:
                self.set_content()


class ViewerForm(ViewerDialog):
    def __init__(self, parent: QWidget = None, content: str = None, title: str = "View"):
        ViewerDialog.__init__(self, parent=parent, content=content, title=title)
        self.setModal(False)


if __name__ == "__main__":
    """
    Testing of Popup-Viewer-Dialog
    """
    from PyQt5.QtWidgets import QMainWindow, QPushButton
    sys._excepthook = sys.excepthook


    def my_exception_hook(exctype, value, traceback):
        # Print the error and traceback
        print(exctype, value, traceback)
        # Call the normal Exception hook after
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)


    # Set the exception hook to our wrapping function
    sys.excepthook = my_exception_hook


    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.viewer = None
            button = QPushButton("Test")
            button.clicked.connect(self.test_form)
            self.setCentralWidget(button)

        def test_dialog(self):
            v = ViewerDialog(parent=self)
            v.set_content(print("Testing"))
            v.exec_()

        def read_file(self) -> str:
            with open("systemtray.py", "r") as text_file:
                res = text_file.read()
            return res

        def test_form(self):
            if not self.viewer:
                self.viewer = ViewerForm(parent=self)
            self.viewer.set_content_function(self.read_file)
            self.viewer.set_content()
            self.viewer.show()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        app.exec_()
    except:
        print("Exit")
