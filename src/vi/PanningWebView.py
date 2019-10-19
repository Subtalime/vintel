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
        self.mapView = MapViewPage()
        self.view = QWebEngineView()
        self.view.setPage(self.page())
        self.vl = QVBoxLayout()
        self.vl.addWidget(self.view)
        self.setLayout(self.vl)
        self.oldContent = None


    def setZoomFactor(self, value: float):
        self.zoom_factor.emit(value)
        return self.page().setZoomFactor(value)

    @property
    def zoomFactor(self) -> float:
        return self.page().zoomFactor()

    # imitate QWebEngineView
    def page(self) -> QWebEnginePage:
        return self.mapView

    def setHtml(self, p_str: str, baseUrl: QUrl=None, *args, **kwargs):
        if self.oldContent != p_str:
            self.page().setHtml(p_str, baseUrl, *args, **kwargs)
            self.oldContent = p_str

