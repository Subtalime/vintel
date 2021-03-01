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

from PyQt5.QtWidgets import QVBoxLayout, QApplication, QDialog, QTextEdit
import logging


class ViewerDialog(QDialog):
    """create a Popup-Dialog showing content
    """
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
        self.LOGGER.debug("activated ViewerDialog %s", title)
        if content:
            self.set_content(content)

    def set_content(self, content: str):
        """
        set the content of the Text-Edit
        :param content: the content to be displayed
        :type content: str
        """
        self.LOGGER.debug("set content (partial): %s...", content[:30])
        view_text = QTextEdit()
        view_text.setPlainText(content)
        self.layout().addWidget(view_text)


if __name__ == "__main__":
    """
    Testing of Popup-Viewer-Dialog
    """
    from PyQt5.QtWidgets import QMainWindow, QPushButton

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            button = QPushButton("Test")
            button.clicked.connect(self.test)
            self.setCentralWidget(button)

        def test(self):
            v = ViewerDialog()
            v.set_content("Testing")
            v.exec_()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
