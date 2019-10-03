from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import pyqtSignal, QPointF, QUrl
from queue import Queue
import difflib
import logging

class MapViewPage(QWebEnginePage):
    link_clicked = pyqtSignal(QUrl)
    scroll_detected = pyqtSignal(QPointF)

    def __init__(self, parent: 'QObject'=None):
        super().__init__(parent)
        # self.channel = QWebChannel()
        self.load_complete = False
        self.javaQueue = Queue()
        self.scrollPositionChanged.connect(self.onScrollPos)
        self.loadFinished.connect(self.onLoadFinished)
        self.loadStarted.connect(self.onLoadStarted)
        self.currentHtml = None
        self.currentScrollPos = QPointF()

    def onLoadFinished(self):
        self.load_complete = True
    def onLoadStarted(self):
        self.load_complete = False

    def setHtml(self, p_str: str, baseUrl: QUrl=None, *args, **kwargs):
        if self.currentHtml != p_str:
            if self.currentHtml and logging.getLogger().getEffectiveLevel() == logging.DEBUG:
                org = set(self.currentHtml.split(' '))
                new = set(p_str.split(' '))
                diff = org.difference(new)
                logging.debug("HTML-Diff: {}".format(diff))
            self.currentHtml = p_str
            super().setHtml(p_str, QUrl(baseUrl), *args, **kwargs)

    def zoomChanged(self, value: float):
        self.setZoomFactor(value)

    def onScrollPos(self, qPointF: QPointF):
        if qPointF == QPointF(): # empty
            # we need to reposition to old good spot
            # here we need to restore the previous position
            # this still doesn't help... something still moves it to 0.0
            qPointF = self.currentScrollPos
        else:
            self.currentScrollPos = qPointF
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            logging.debug("Scroll detected {} Complete: {}".format(qPointF, self.load_complete))
        self.scroll_detected.emit(qPointF)
        return True

    def runJavaScript(self, p_str, *__args):
        if not self.load_complete:
            self.javaQueue.put_nowait((p_str, *__args))
            return
        if not self.javaQueue.empty():
            while not self.javaQueue.empty():
                q = self.javaQueue.get_nowait()
                super().runJavaScript(q[0], q[1])
        super().runJavaScript(p_str, *__args)

    def acceptNavigationRequest(self, qUrl: QUrl, QWebEnginePage_NavigationType: int, abool: bool):
        if QWebEnginePage_NavigationType == QWebEnginePage.NavigationTypeLinkClicked:
            self.link_clicked.emit(qUrl)
            return False
        return super(MapViewPage, self).acceptNavigationRequest(qUrl, QWebEnginePage_NavigationType, abool)
