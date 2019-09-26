from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import pyqtSignal, QPointF


class MapViewPage(QWebEnginePage):
    link_clicked = pyqtSignal(str)
    mark_system = pyqtSignal(str)
    scroll_detected = pyqtSignal(QPointF)

    def __init__(self, parent: 'QObject'=None):
        super().__init__(parent)
        self.channel = QWebChannel()
        self.scrollPositionChanged.connect(self.onScrollPos)


    def zoomChanged(self, value: 'float'):
        self.setZoomFactor(value)

    def onScrollPos(self, qPointF: 'QPointF'):
        self.scroll_detected.emit(qPointF)
        return True

    def acceptNavigationRequest(self, qUrl: 'QUrl', QWebEnginePage_NavigationType: 'int', abool: 'bool'):
        if QWebEnginePage_NavigationType == QWebEnginePage.NavigationTypeLinkClicked:
            self.link_clicked.emit(qUrl)
            return False
        return super(MapViewPage, self).acceptNavigationRequest(qUrl, QWebEnginePage_NavigationType, abool)


