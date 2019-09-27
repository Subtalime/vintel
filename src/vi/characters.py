from vi.cache.cache import Cache
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QMenu, QAction, QListWidgetItem, QMainWindow, QMenuBar, QPushButton
from PyQt5.QtCore import Qt, QRect, pyqtSignal, pyqtSlot
import logging
from collections import OrderedDict


# TODO: store "Characters" in the Menu and have the class adjusted on Menu-Actions

# a dynamic QMenu to maintain character selections
class CharacterMenu(QMenu):
    toggle_action = pyqtSignal(str, bool)

    def __init__(self, menuname, parent=None, characters=None):
        super(CharacterMenu, self).__init__(menuname, parent)
        self._listWidget = QListWidget()
        self._menu_actions = dict()
        if characters is not None:
            self.characters = Characters(characters)
            self.addItems(self.characters)

    def addItem(self, name, checked=False):
        if type(name) is Character:
            charname = name.getName()
            checked = name.getStatus()
        else:
            charname = name
        if charname in self._menu_actions.keys():
            return
        action = QAction(charname, self, checkable=True)
        action.setData(self._actionName(charname))
        action.setChecked(checked)
        # action.triggered.connect(self.toggleAction)
        self._menu_actions[charname] = action
        self.addAction(action)


    def toggleAction(self, qAction):

        name = qAction.text()
        char = self.characters[name]
        self.characters[qAction.text()].setMonitor(qAction.isChecked())
        self.toggle_action.emit(qAction.text(), qAction.isChecked())

    # add characters to the Menu
    def addItems(self, characters):
        if type(characters) is not Characters:
            logging.error("Type of Characters expected as \"characters\"")
            return False
        od = OrderedDict(sorted(characters.items()))
        for key in od.keys():
            # already exists
            self.addItem(od[key])
        return True

    def _actionName(self, action):
        return str(action).replace(' ', '_').replace('-', '_') + "_action"

    def removeItem(self, name):
        if name in self._menu_actions.keys():
            self.removeAction(self._menu_actions.get(name))
            self._menu_actions.pop(name)

    # deletes all items from the Menu or selected ones passed in a list
    def removeItems(self, characters=None):
        # need to do this, since "pop" will corrupt the iterator
        keys = [key for key in self._menu_actions.keys()]
        for key in keys:
            if (characters is not None and key in characters) or characters is None:
                self.removeItem(key)


class Characters(dict):

    def __init__(self, path_to_logs=None):
        self._knownPlayers = dict()
        self._logPath = path_to_logs
        self._cache = Cache()
        # initialize by Cache-Content
        self.loadData()

    def add(self, charname, status=True, location=None, store=True):
        if type(charname) is Character:
            self[charname.getName()] = charname
        else:
            self[charname] = Character(charname, status, location)
        if store:
            self.storeData()

    def pop(self, charname, store=True):
        if charname in self.keys():
            del self[charname]
            if store:
                self.storeData()
        else:
            logging.warning("tried to remove character \"{}\" which does not exist".format(charname))

    def get(self, charname):
        if charname in self.keys():
            return self[charname]
        return None

    def getNames(self):
        chars = []
        for player in self.keys():
            chars.append(player)
        return chars

    def loadData(self):
        knownPlayerData = self._cache.getFromCache("known_players")
        if knownPlayerData:
            charsets = set(knownPlayerData.split(","))
            for character in charsets:
                try:
                    arr = list(character.split("."))
                    self.add(Character(arr[0], arr[1], arr[2]))
                    # self[arr[0]] = Character(arr[0], arr[1], arr[2])
                except Exception as e:
                    logging.error("could not add player \"{}\"".format(character), e)
                    pass

    def storeData(self):
        value = ",".join(str(x) for x in self.values())
        self._cache.putIntoCache("known_players", value, 60 * 60 * 24 * 30)

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
        stdmenu = QMenu()
        self.chars = self.menubar.addMenu("Characters")
        # names = ["über", "me", "you", "them", "test", "del"]
        self.characters = Characters()
        # for name in names:
        #     self.characters.add(name)

        self.charmenu = CharacterMenu("Select", characters=self.characters)
        self.chars.addMenu(self.charmenu)
        self.menubar.addMenu(self.charmenu)
        self.charmenu.triggered.connect(self.process_select)
        # reshuffle
        self.widget = QWidget()
        self.layout = QVBoxLayout(self.widget)
        self.menuButton = QPushButton("Rebuild Menu")
        self.layout.addWidget(self.menuButton)
        self.menuButton.clicked.connect(self.rebuildmenu)
        self.setCentralWidget(self.widget)


    def rebuildmenu(self):
        self.characters.pop("test")
        self.characters.pop("del")
        self.charmenu.removeItems()
        self.charmenu.addItems(self.characters)
        self.chars.addMenu(self.charmenu)

    def process_select(self, q):
        # res = QAction(q)
        self.characters[q.text()].setMonitoring(q.isChecked())
        self.characters.storeData()
        print("Menu \"{}\" is selected: {}".format(q.text(), q.isChecked()))


# The main application
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QMainWindow, QApplication
    app = QApplication(sys.argv)
    form = CharTestMainForm()
    form.resize(400, 400)
    form.show()
    app.exec_()

    # chars = Characters()
    # chars.add("test")
    # chars.add("test", location="here")
    # char = chars.get("test")
    # char = chars.get("tt")
    # chars.pop("delw")
    # chars.pop("del")
