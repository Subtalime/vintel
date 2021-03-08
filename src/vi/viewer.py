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
import logging

from PyQt5.QtWidgets import QVBoxLayout, QApplication, QDialog, QTextEdit, QWidget, QMenu, QAction
from PyQt5.QtGui import QContextMenuEvent, QCloseEvent, QShowEvent
from PyQt5.QtCore import Qt


class ViewerRefreshFunctionException(Exception):
    """raised if the function to load content passed to the Viewer is not callable
    """
    def __init__(self, message=None):
        if message is None:
            message = "This expects a callable function"
        super(ViewerRefreshFunctionException, self).__init__(message)


class ViewText(QTextEdit):
    """Add custom action to reload the content of the Text-Edit field
    """
    _reload = None

    def __init__(self, parent: QWidget = None):
        """a text field, we can be triggered to reload its content via context-menu
        """
        super(ViewText, self).__init__(parent=parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.generate_context_menu)

    def add_reload_action(self, func):
        """set the function to be triggered on "Reload" action context menu
        """
        if not self._reload and callable(func):
            self._reload = QAction("Reload content", None)
            self._reload.triggered.connect(func)

    def generate_context_menu(self, location):
        """if there is a reload configured, add it to the bottom of the context menu
        """
        menu = self.createStandardContextMenu(location)
        if self._reload:
            menu.addSeparator()
            menu.addAction(self._reload)
        menu.exec_(self.mapToGlobal(location))


class ViewerDialog(QDialog):
    """create a Popup-Dialog showing content
    """
    _content_function = None
    reload = None

    def __init__(self, parent: QWidget = None, content: str = None, title: str = "View"):
        """
        Standard QDialog to show content in a Text-Editor (read-only)
        :param parent: parent window
        :type parent: QWidget
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
        if content:
            self.set_content(content)

    @property
    def content_function(self):
        return self._content_function

    @content_function.setter
    def content_function(self, value):
        if callable(value):
            self._content_function = value
        else:
            raise ViewerRefreshFunctionException("Passed value is not a callable function")

    def set_content(self, content: str = None):
        """
        set the content of the Text-Edit
        :param content: the content to be displayed (can be a function)
        :type content: any
        """
        if not content and self.content_function:
            content = self._content_function()
        elif not content:
            content = ""
        self.LOGGER.debug("set content (partial): %s...", content[:30])
        self.view_text.setPlainText(content)

    def set_content_loader_function(self, function):
        """set the function, which returns a string containing data to be shown
        :param function: a function returning content to be shown in the Viewer
        :type function: callable
        """
        self.content_function = function
        self.LOGGER.debug(f"added loader function '{function}'")
        self.view_text.add_reload_action(self.set_content)
        self.set_content()

    def showEvent(self, a0: QShowEvent) -> None:
        self.LOGGER.debug("activated ViewerDialog '%s'", self.windowTitle())
        super(ViewerDialog, self).showEvent(a0)

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.LOGGER.debug("Viewer closed")
        super(ViewerDialog, self).closeEvent(a0)


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
            self.viewer.set_content_loader_function(self.read_file)
            self.viewer.set_content()
            self.viewer.show()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        app.exec_()
    except:
        print("Exit")
