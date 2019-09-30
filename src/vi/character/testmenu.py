from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAction, QMainWindow, QPushButton
from PyQt5.QtCore import QRect
from vi.character.Characters import  Characters
from vi.character.CharacterMenu import CharacterMenu

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
            self.characters.addName(nam)
        self.charmenu = CharacterMenu("Select", self, characters=self.characters)
        self.menubar.addMenu(self.charmenu)
        # self.chars.addMenu(self.charmenu)
        self.charmenu.triggered[QAction].connect(self.process_select)
        self.menuButton = QPushButton("Rebuild Menu")
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(self.menuButton)
        self.menuButton.clicked.connect(self.rebuildmenu)
        self.setCentralWidget(widget)

    def rebuildmenu(self):
        self.characters.remove("test")
        self.characters.remove("del")
        self.characters.addName("precious")
        self.charmenu.removeItems()
        self.charmenu.addItems(self.characters)
        # self.chars.addMenu(self.charmenu)

    def process_select(self, q: 'QAction'):
        self.characters[q.text()].setMonitoring(q.isChecked())

    def closeEvent(self, *args, **kwargs):
        self.characters.storeData()

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
