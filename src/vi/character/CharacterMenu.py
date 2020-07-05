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
    """Track players characters on this machine.
    I can't remember the right intention I had with this.
    I believe it was to dis/enable character tracking on the Map-Interface?
    """
    def __init__(
        self, menu_name: str, parent: QObject = None, characters: Characters = None
    ):
        super(CharacterMenu, self).__init__(menu_name, parent)
        self._listWidget = QListWidget()
        self._menu_actions = {}
        self.setObjectName("menu_" + menu_name)
        if characters is not None:
            self.add_characters(characters)

    def _actionName(self, action: str) -> str:
        return str(action).replace(" ", "_").replace("-", "_") + "_action"

    def add_character(self, character: Character) -> bool:
        if not isinstance(character, Character):
            logging.critical('addItem(characters) must be of type "Characters"')
            return False
        # prevent duplicates
        if character.getName() in self._menu_actions.keys():
            return False
        action = QAction(character.getName(), self)
        action.setCheckable(True)
        action.setData(self._actionName(character.getName()))
        action.setObjectName(character.getName())
        action.setChecked(character.getStatus())
        # TODO: not sure what to do with this yet...
        action.setEnabled(False)
        action.setToolTip("deselect to disable monitoring")
        self._menu_actions[character.getName()] = action
        self.addAction(action)
        return True

    def add_characters(self, characters: Characters) -> bool:
        if not isinstance(characters, Characters):
            logging.critical('addItems(characters) must be of type "Characters"')
            return False
        od = OrderedDict(sorted(characters.items()))
        for key in od.keys():
            self.add_character(od[key])
        return True

    def remove_character(self, character: Character) -> bool:
        if not isinstance(character, Character):
            logging.critical('remove_character(character) must be of type "Character"')
        elif character.getName() in self._menu_actions.keys():
            self.removeAction(self._menu_actions.get(character.getName()))
            self._menu_actions.pop(character.getName())
            return True
        return False

    def remove_characters(self):
        try:
            self.clear()
            # for menuitem in self._menu_actions:
            #     obj = self.findChild(QAction, menuitem)
            #     if obj:
            #         self.removeAction(obj)
            self._menu_actions = dict()
        except Exception:
            raise
