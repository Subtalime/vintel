import six
import sys
import datetime
import webbrowser

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget
import vi.ui.ChatEntry
from vi.resources import resourcePath

class ChatEntryWidget(QtWidgets.QWidget, vi.ui.ChatEntry.Ui_Form):
    TEXT_SIZE = 11
    SHOW_AVATAR = True
    questionMarkPixmap = None
    mark_system = pyqtSignal(str)
    ship_detail = pyqtSignal(str)
    enemy_detail = pyqtSignal(str)

    def __init__(self, message):
        QWidget.__init__(self)
        if not self.questionMarkPixmap:
            self.questionMarkPixmap = QPixmap(resourcePath("vi/ui/res/qmark.png")).scaledToHeight(32)
        self.setupUi(self)
        self.avatarLabel.setPixmap(self.questionMarkPixmap)
        self.message = message
        self.updateText()
        self.textLabel.linkActivated.connect(self.linkClicked)
        if sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
            ChatEntryWidget.TEXT_SIZE = 8
        self.changeFontSize(self.TEXT_SIZE)
        if not ChatEntryWidget.SHOW_AVATAR:
            self.avatarLabel.setVisible(False)

    def linkClicked(self, link):
        link = six.text_type(link)
        function, parameter = link.split("/", 1)
        if function == "mark_system":
            self.mark_system.emit(parameter)
        elif function == "link":
            webbrowser.open(parameter)
        elif function == "show_enemy":
            # TODO: open ZKillboard?
            self.enemy_detail.emit(parameter)
        elif function == "ship_name":
            # TODO: open Ship-Detail Window?
            self.ship_detail.emit(parameter)




    def updateText(self):
        time = datetime.datetime.strftime(self.message.timestamp, "%H:%M:%S")
        text = u"<small>{time} - <b>{user}</b> - <i>{room}</i></small><br>{text}".format(user=self.message.user,
                                                                                         room=self.message.room,
                                                                                         time=time,
                                                                                         text=self.message.message)
        self.textLabel.setText(text)


    def updateAvatar(self, avatarData):
        image = QImage.fromData(avatarData)
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return False
        scaledAvatar = pixmap.scaled(32, 32)
        self.avatarLabel.setPixmap(scaledAvatar)
        return True


    def changeFontSize(self, newSize):
        font = self.textLabel.font()
        font.setPointSize(newSize)
        self.textLabel.setFont(font)
