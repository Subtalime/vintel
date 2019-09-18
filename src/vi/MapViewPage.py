import six
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtCore import pyqtSignal


class MapViewPage(QWebEnginePage):
    link_clicked = pyqtSignal(str)
    mark_system = pyqtSignal(str)

    def __init__(self, parent=None):
        super(MapViewPage, self).__init__(parent)

    def createWindow(self, QWebEnginePage_WebWindowType):
        page = MapViewPage(self)
        page.urlChanged.connect(self.open_browser)
        return page

    def openBrowser(self, url):
        page = self.sender()


    def acceptNavigationRequest(self, QUrl, QWebEnginePage_NavigationType, abool):
        if QWebEnginePage_NavigationType == QWebEnginePage.NavigationTypeLinkClicked:
            self.link_clicked.emit(QUrl)
            return False
        return super(MapViewPage, self).acceptNavigationRequest(QUrl, QWebEnginePage_NavigationType, abool)

    def linkClicked(self, link):
        link = six.text_type(link)
        function, parameter = link.split("/", 1)
        if function == "mark_system":
            self.mark_system.emit(parameter)
        elif function == "link":
            self.link_clicked.emit(parameter)
            # webbrowser.open(parameter)
