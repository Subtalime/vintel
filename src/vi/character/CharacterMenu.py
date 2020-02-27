#   Vintel - Visual Intel Chat Analyzer
#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
#

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QListWidget, QMenu, QAction
from vi.character.Characters import Characters, Character
from collections import OrderedDict
import logging


# TODO: add emit-action on click
class CharacterMenu(QMenu):
    def __init__(self, menuname: str, parent: QObject = None, characters: Characters = None):
        super(CharacterMenu, self).__init__(menuname, parent)
        self._listWidget = QListWidget()
        self._menu_actions = {}
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
        if character.getName() in self._menu_actions.keys():
            return False
        action = QAction(character.getName(), self)
        action.setCheckable(True)
        action.setData(self._actionName(character.getName()))
        action.setObjectName(character.getName())
        action.setChecked(character.getStatus())
        action.setToolTip("deselect to disable monitoring")
        self._menu_actions[character.getName()] = action
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
        elif character.getName() in self._menu_actions.keys():
            self.removeAction(self._menu_actions.get(character.getName()))
            self._menu_actions.pop(character.getName())
            return True
        return False

    def removeItems(self):
        try:
            self.clear()
            # for menuitem in self._menu_actions:
            #     obj = self.findChild(QAction, menuitem)
            #     if obj:
            #         self.removeAction(obj)
            self._menu_actions = dict()
        except Exception:
            raise
