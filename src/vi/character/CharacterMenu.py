from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import  QListWidget, QMenu, QAction
from vi.character.Characters import Characters, Character
from collections import OrderedDict
import logging

# TODO: add emit-action on click
class CharacterMenu(QMenu):
    def __init__(self, menuname: str, parent: QObject=None, characters: Characters=None):
        super(CharacterMenu, self).__init__(menuname, parent)
        self._listWidget = QListWidget()
        self._menu_actions = dict()
        self.setObjectName("menu"+menuname)
        if characters is not None:
            self.addItems(characters)

    def _actionName(self, action: str) -> str:
        return str(action).replace(' ', '_').replace('-', '_') + "_action"

    def addItem(self, character: Character) -> bool:
        if not isinstance(character, Character):
            logging.critical("addItem(characters) must be of type \"Characters\"")
            return False
        # prevent duplicates
        if character.getName in self._menu_actions.keys():
            return False
        action = QAction(character.getName, self, checkable=True)
        action.setData(self._actionName(character.getName))
        action.setObjectName(character.getName)
        action.setChecked(character.getStatus)
        self._menu_actions[character.getName] = action
        self.addAction(action)
        return True

    def addItems(self, characters: Characters) -> bool:
        if not isinstance(characters, Characters):
            logging.critical("addItems(characters) must be of type \"Characters\"")
            return False
        od = OrderedDict(sorted(characters.items()))
        for key in od.keys():
            self.addItem(od[key])
        return True

    def removeItem(self, character: Character) -> bool:
        if not isinstance(character, Character):
            logging.critical("removeItem(character) must be of type \"Character\"")
        elif character.getName in self._menu_actions.keys():
            self.removeAction(self._menu_actions.get(character.getName))
            self._menu_actions.pop(character.getName)
            return True
        return False

    def removeItems(self):
        try:
            for menuitem in self._menu_actions:
                obj = self.findChild(QAction, menuitem)
                if obj:
                    self.removeAction(obj)
            self._menu_actions = dict()
        except Exception as e:
            raise
