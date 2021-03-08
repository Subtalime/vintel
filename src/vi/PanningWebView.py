#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from vi.map.MapWebEnginePage import MapWebEnginePage
import logging


class PanningWebView(QWidget):
    zoom_factor = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.LOGGER = logging.getLogger(__name__)

        self.mapView = MapWebEnginePage()
        self.view = QWebEngineView()
        self.view.setPage(self.mapView)
        self.vl = QVBoxLayout()
        self.vl.addWidget(self.view)
        self.setLayout(self.vl)
        self.oldContent = None

    @property
    def content(self) -> str:
        return self.oldContent

    def setZoomFactor(self, value: float):
        self.zoom_factor.emit(value)
        return self.page().setZoomFactor(value)

    @property
    def zoomFactor(self) -> float:
        return self.page().zoomFactor()

    def scrollPosition(self):
        return self.page().scrollPosition()

    # imitate QWebEngineView
    def page(self) -> QWebEnginePage:
        return self.mapView

    def setHtml(self, p_str: str, base_url: QUrl = None, *args, **kwargs):
        if self.oldContent != p_str:
            self.page().setHtml(p_str, base_url, *args, **kwargs)
            self.oldContent = p_str
