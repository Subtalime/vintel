from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QMenu, QAction, QListWidgetItem
from PyQt5.QtCore import Qt

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

