from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAction, QMainWindow, QPushButton
from PyQt5.QtCore import QRect
from vi.dotlan import Regions
from vi.region.RegionMenu import RegionMenu
from vi.region.RegionChooserList import RegionChooserList
from vi.jumpbridgechooser import JumpbridgeChooser
from vi.cache.cache import Cache

class RegionTestMainForm(QMainWindow):
    def __init__(self, parent=None):
        super(RegionTestMainForm, self).__init__(parent)
        self.menubar = self.menuBar()
        self.menubar.setGeometry(QRect(0, 0, 936, 21))
        self.menubar.setObjectName("menubar")
        self.chars = self.menubar.addMenu("Regions")
        self.regionMenu = RegionMenu("Select", self)
        self.menubar.addMenu(self.regionMenu)
        self.regionMenu.triggered[QAction].connect(self.process_select)

    def process_select(self, qAction: 'QAction'):
        if qAction.objectName() == "region_select":
            self.regionChooser()
        elif qAction.objectName() == "jumpbridge_select":
            self.jumpBridgeChooser()
        else:
            data = qAction.data()
            text = qAction.text()
            menu = qAction.menu()
            name = qAction.objectName()
            Cache().putIntoCache("region_name", text, 364 * 24 * 60 * 60)

            print("{} Action {}".format(qAction.text(), qAction.isChecked()))

    def jumpBridgeChooser(self):
        url = self.cache.getFromCache("jumpbridge_url")
        chooser = JumpbridgeChooser(self, url)
        chooser.set_jump_bridge_url.connect(self.setJumpbridges)
        chooser.show()

    def regionChooser(self):
        def handleRegionsChosen(regionList):
            print(regionList)
            self.regionMenu.addItems()
        chooser = RegionChooserList(self)
        chooser.new_region_range_chosen.connect(handleRegionsChosen)
        chooser.show()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QMainWindow, QApplication
    app = QApplication(sys.argv)
    form = RegionTestMainForm()
    form.resize(936, 695)
    form.show()
    app.exec_()
