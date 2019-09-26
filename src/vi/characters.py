from vi.cache.cache import Cache
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QMenu, QAction, QListWidgetItem, QMainWindow, QMenuBar, QPushButton
from PyQt5.QtCore import Qt, QRect
import logging

class CharacterMenu(QWidget):
    def __init__(self, characters, menuname, parent=None):
        super(CharacterMenu, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.listWidget = QListWidget()

        self.layout.addWidget(self.listWidget)
        self.menu = QMenu(menuname)
        self.menu_items = []
        self.loadItems(characters)

    def addItems(self, characters):
        return self.loadItems(characters)
    def loadItems(self, characters):
        if self.listWidget.count() > 0:
            self.removeItems()
        for name in characters:
            action = QAction(name, self.menu)
            action_name = str(name).replace(' ', '_').replace('-', '_')
            action.setData(action_name + "_action")
            self.menu_items.append(action)
            self.menu.addAction(action)
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, action_name + "_action")
            self.listWidget.addItem(item)

    def removeItems(self):
        for menuitem in self.menu_items:
            self.menu.removeAction(menuitem)
        self.menu_items = []

    def sync_data(self):
        save_items = {}
        for i in range(self.listWidget.count()):
            it = self.listWidget.item(i)
            action = it.data(Qt.UserRole)
            save_items[it.text()] = action.data()
        # here we could save them in settings

class Characters:
    knownPlayers = dict()
    logPath = None
    cache = None

    def __init__(self, path_to_logs=None):
        self.logPath = path_to_logs
        self.cache = Cache()
        knownPlayerData = self.cache.getFromCache("known_players")
        if knownPlayerData:
            charsets = set(knownPlayerData.split(","))
            for char in charsets:
                try:
                    name, mon, location = char.split(".")
                    self.addCharacter(name, status=mon, location=location, store=False)
                except Exception as e:
                    logging.error("could not add player \"{}\"".format(name), e)

    def addCharacter(self, charname, status=True, location=None, store=True):
        if charname not in self.knownPlayers:
            self.knownPlayers[charname] = self.Character(charname, status, location)
            if store:
                self.storeData()

    def delCharacter(self, charname, store=True):
        if charname in self.knownPlayers:
            self.knownPlayers.pop(charname)
            if store:
                self.storeData()
        else:
            logging.warning("tried to remove character \"{}\" which does not exist".format(charname))


    def getCharacter(self, charname):
        if charname in self.knownPlayers:
            return self.knownPlayers.get(charname)
        return None

    def getCharacterNames(self):
        chars = []
        for player in self.knownPlayers.keys():
            chars.append(player)
        return chars

    def storeData(self):
        value = ",".join(str(x) for x in self.knownPlayers.values())
        self.cache.putIntoCache("known_players", value, 60 * 60 * 24 * 30)

    class Character:
        monitor = False
        charname = None
        location = None

        def __init__(self, charname, status=True, location=None):
            self.charname = charname
            self.monitor = bool(eval(str(status)))
            self.location = None if location == 'None' else location

        def update(self, monitor=None, location=None):
            if monitor:
                self.setMonitoring(monitor)
            if location:
                self.setLocation(location)
            return self

        def setMonitoring(self, enable):
            self.monitor = enable

        def setLocation(self, location):
            self.location = location

        def getLocations(self):
            return self.location

        def disable(self):
            self.setMonitoring(False)

        def enable(self):
            self.setMonitoring(True)

        def getName(self):
            return self.charname

        def getStatus(self):
            return self.monitor

        def getMonitoring(self):
            return self.getStatus()

        def __repr__(self):
            return "{}.{}.{}".format(self.charname, self.monitor, self.location)


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

        # self.menu = QMenu(self.menubar)
        # self.menu.setObjectName("Characters")
        # self.setMenuBar(self.menubar)
        # self.menu.addMenu(self.charmenu.menu)


    def rebuildmenu(self):
        self.characters.delCharacter("test")
        self.characters.delCharacter("del")
        self.charmenu.removeItems()
        self.charmenu.addItems(self.characters.getCharacterNames())
        # self.charmenu = CharacterMenu(self.characters.getCharacterNames(), "Select")
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

    chars = Characters()
    chars.addCharacter("test")
    chars.addCharacter("test", location="here")
    char = chars.getCharacter("test")
    char = chars.getCharacter("tt")
    chars.delCharacter("delw")
    chars.addCharacter("del")
