from PyQt5.QtWidgets import QWidget
import vi.ship.ShipDialog
from vi.esi.EsiHelper import EsiHelper, EsiInterface
import logging

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


