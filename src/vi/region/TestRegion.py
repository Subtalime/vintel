from PyQt5.QtWidgets import QWidget, QVBoxLayout, QAction, QMainWindow, QPushButton, QActionGroup
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
        self.groupMenu = self.menubar.addMenu("Group Test")
        self.grouptest = QActionGroup(self, exclusive=True)
        items = ["a", "b", "c", "d"]
        for item in items:
            a = QAction(item, self, checkable=True)
            self.grouptest.addAction(a)
            self.groupMenu.addAction(a)


    def process_select(self, qAction: 'QAction'):
        if qAction.objectName() == "region_select":
            self.regionChooser()
        elif qAction.objectName() == "jumpbridge_select":
            self.jumpBridgeChooser()
        else:
            Cache().putIntoCache("region_name", qAction.text(), Regions.CACHE_TIME)
            print("{} Action {}".format(qAction.text(), qAction.isChecked()))
            self.setupMap()

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

    def setupMap(self):
        print("Call viui.setupMap() now")

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QMainWindow, QApplication
    app = QApplication(sys.argv)
    form = RegionTestMainForm()
    form.resize(936, 695)
    form.show()
    app.exec_()
