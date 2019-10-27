import six
import requests
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QDialog
import logging
from PyQt5.QtCore import pyqtSignal
from vi.resources import resourcePath
from vi.cache.cache import Cache
from vi.dotlan.regions import convertRegionName
from vi.dotlan.mymap import Map


from vi.ui.RegionChooser import Ui_Dialog
class RegionChooser(QtWidgets.QDialog, Ui_Dialog):
    new_region_chosen = pyqtSignal()

    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cancelButton.clicked.connect(self.accept)
        self.saveButton.clicked.connect(self.saveClicked)
        cache = Cache()
        regionName = cache.getFromCache("region_name")
        if not regionName:
            regionName = u"Delve"
        self.regionNameField.setPlainText(regionName)


    def saveClicked(self):
        text = six.text_type(self.regionNameField.toPlainText())
        text = convertRegionName(text)
        self.regionNameField.setPlainText(text)
        correct = False
        try:
            url = Map.DOTLAN_BASIC_URL.format(text)
            content = requests.get(url).text
            if u"not found" in content:
                correct = False
                # Fallback -> ships vintel with this map?
                try:
                    with open(resourcePath("vi/ui/res/mapdata/{0}.svg".format(text))) as _:
                        correct = True
                except Exception as e:
                    logging.error(e)
                    correct = False
                if not correct:
                    logging.warning("Unable to find region \"{}\"".format(text))
                    QMessageBox.warning(self, u"No such region!", u"I can't find a region called '{0}'".format(text),
                                        QMessageBox.Ok)
            else:
                correct = True
        except Exception as e:
            QMessageBox.critical(self, u"Something went wrong!", u"Error while testing existing '{0}'".format(str(e)),
                                 QMessageBox.Ok)
            logging.error(e)
            correct = False
        if correct:
            Cache().putIntoCache("region_name", text, 60 * 60 * 24 * 365)
            self.accept()
            self.new_region_chosen.emit()

