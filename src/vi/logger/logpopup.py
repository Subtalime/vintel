#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
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
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMenu
import logging


class LogLevelAction(QtWidgets.QAction):
    def __init__(self, set_level: int, curr_level: int = None):
        """Action-Handler for Log-Levels

        :param set_level: set the Logging Level (must be valid logging.level)
        :type int
        :param curr_level: current Logging-Level, to set a Checked-Marker if this matches with set_level
        :type int
        """
        name = logging.getLevelName(set_level)
        super(LogLevelAction, self).__init__(name)
        self.setCheckable(True)
        self.level = set_level
        if self.level == curr_level:
            self.setChecked(True)

    def log_level(self):
        return self.level


class LogLevelPopup(QMenu):
    def __init__(self, parent, current_log_level: int = None):
        """Context-Popup-Menu for logging levels.

        :param parent: parent window handler
        :param current_log_level: current logging level
        :type current_log_level int
        """
        super(LogLevelPopup, self).__init__(parent)
        if not current_log_level:
            current_log_level = logging.getLogger(self.parent().__name__).level
        self._log_level = current_log_level
        self.actions = []
        self._setup_menu()

    def _setup_menu(self):
        # needs to be stored in a variable, else Python garbage deletes
        self.actions.append(LogLevelAction(logging.DEBUG, self._log_level))
        self.actions.append(LogLevelAction(logging.INFO, self._log_level))
        self.actions.append(LogLevelAction(logging.WARNING, self._log_level))
        self.actions.append(LogLevelAction(logging.ERROR, self._log_level))
        self.actions.append(LogLevelAction(logging.CRITICAL, self._log_level))
        for action in self.actions:
            self.addAction(action)

    def exec_(self, *args) -> LogLevelAction:
        res = super(LogLevelPopup, self).exec_(*args)
        return res

    def get_result(self, action: LogLevelAction):
        return action.level
