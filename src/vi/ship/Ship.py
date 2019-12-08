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

from PyQt5.QtWidgets import QWidget
import vi.ship.ShipDialog
from vi.esi.esihelper import EsiHelper
import logging

# TODO: show some information about the Ship...
class Ship(QWidget, vi.ship.ShipDialog.Ui_Dialog):

    def __init__(self, shipName: str=None, shipId: int=None):
        if not shipName and not shipId:
            logging.critical("No Ship-Name or Ship-ID passed")
            return False
        if shipName: # retreive the equivalent ID
            shipId = EsiHelper().getShipId(shipName)
            if not shipId:
                logging.critical("Ship with name \"{}\" not found".format(shipName))
        self.setupUi(self)


