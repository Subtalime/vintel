from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAction, QMainWindow, QPushButton
from PyQt5.QtCore import Qt, QRect
from .characters import Characters
from .charactermenu import CharacterMenu

class CharTestMainForm(QMainWindow):
    def __init__(self, parent=None):
        super(CharTestMainForm, self).__init__(parent)
        self.menubar = self.menuBar()
        self.menubar.setGeometry(QRect(0, 0, 936, 21))
        self.menubar.setObjectName("menubar")
        self.chars = self.menubar.addMenu("Characters")
        characters = ["me", "you", "them", "test", "del"]
        self.characters = Characters()
        for nam in characters:
            self.characters.addCharacter(nam)
        self.charmenu = CharacterMenu(self.characters.getCharacterNames(), "Select")
        self.chars.addMenu(self.charmenu.menu)
        self.charmenu.menu.triggered[QAction].connect(self.process_select)
        self.menuButton = QPushButton("Rebuild Menu")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self.menuButton)
        self.menuButton.clicked.connect(self.rebuildmenu)
        self.setCentralWidget(widget)

    def rebuildmenu(self):
        self.characters.delCharacter("test")
        self.characters.delCharacter("del")
        self.charmenu.removeItems()
        self.charmenu.addItems(self.characters.getCharacterNames())
        self.chars.addMenu(self.charmenu.menu)

    def process_select(self, q):
        print(q.text()+" is triggered")

# The main application
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QMainWindow, QApplication
    app = QApplication(sys.argv)
    form = CharTestMainForm()
    form.resize(936, 695)
    form.show()
    app.exec_()

    # chars = Characters()
    # chars.addCharacter("test")
    # chars.addCharacter("test", location="here")
    # char = chars.getCharacter("test")
    # char = chars.getCharacter("tt")
    # chars.delCharacter("delw")
    # chars.addCharacter("del")
