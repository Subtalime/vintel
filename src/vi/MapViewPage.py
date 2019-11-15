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

from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtCore import pyqtSignal, QPointF, QUrl, QEvent, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtGui
from queue import Queue
import logging

LOGGER = logging.getLogger(__name__)


class MapViewPage(QWebEnginePage):
    link_clicked = pyqtSignal(QUrl)
    scroll_detected = pyqtSignal(QPointF)

    def __init__(self, parent: 'QObject' = None):
        super().__init__(parent)
        self.load_complete = False
        self.javaQueue = Queue()
        self.scrollPositionChanged.connect(self.onScrollPos)
        self.loadFinished.connect(self.onLoadFinished)
        self.loadStarted.connect(self.onLoadStarted)
        self.currentHtml = None
        self.currentScrollPos = QPointF()
        self.repositioning = False

    def wheelEvent(self, a0: QtGui.QWheelEvent) -> None:
        modifier = QApplication.keyboardModifiers()
        if modifier == Qt.ControlModifier:
            LOGGER.debug("Control-Delta %r" % a0.Delta())

    def onLoadFinished(self):
        self.load_complete = True

    def onLoadStarted(self):
        self.load_complete = False

    def setHtml(self, p_str: str, baseUrl: QUrl = None, *args, **kwargs):
        if self.currentHtml != p_str:
            self.currentHtml = p_str
            super().setHtml(p_str, QUrl(baseUrl), *args, **kwargs)

    def zoomChanged(self, value: float):
        self.setZoomFactor(value)

    def onScrollPos(self, qPointF: QPointF):
        if qPointF == QPointF():  # empty
            # we need to reposition to old good spot
            # here we need to restore the previous position
            # this still doesn't help... something still moves it to 0.0
            qPointF = self.currentScrollPos
        else:
            self.currentScrollPos = qPointF
        if self.load_complete:
            LOGGER.debug("onScrollPos detected {}, Load Complete: {}".format(qPointF, self.load_complete))
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
