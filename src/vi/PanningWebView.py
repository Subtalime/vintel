from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QCoreApplication, Qt, pyqtSignal, QPointF, QEvent, QObject, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from vi.MapViewPage import MapViewPage

class PanningWebView(QWidget):
    zoom_factor = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pressed = False
        self._parent = parent
        self._page = MapViewPage()
        self.view = QWebEngineView()
        self.view.setPage(self.page())
        self.mapView = self._page
        self.vl = QVBoxLayout()
        self.vl.addWidget(self.view)
        self.setLayout(self.vl)


    def setZoomFactor(self, value: 'float'):
        self.zoom_factor.emit(value)
        return self.page().setZoomFactor(value)

    def zoomFactor(self):
        return self.page().zoomFactor()

    # imitate QWebEngineView
    def page(self):
        return self._page

    def setHtml(self, p_str, baseUrl=None, *args, **kwargs):
        self.page().setHtml(p_str, baseUrl, args, kwargs)

    @QtCore.pyqtSlot(bool)
    def _loadFinished(self, ok):
        if not ok:
            return
        if self.initialMapPosition is None:
            scrollPosition = QPointF(self.mapView.scrollPosition())
        else:
            scrollPosition = self.initialMapPosition
        self.mapView.runJavaScript(str("window.scrollTo({}, {});".
                                              format(scrollPosition.x(),scrollPosition.y())))
        self.initialMapPosition = self.mapView.scrollPosition()
        if scrollPosition.x() == 0 and scrollPosition.y() == 0:
            self.initialMapPosition = None




