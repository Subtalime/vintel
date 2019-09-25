import six
from PyQt5.QtGui import *
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QCoreApplication, Qt, pyqtSignal, QPointF, QEvent, QObject, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage


class MyMapViewPage(QWebEnginePage):
    link_clicked = pyqtSignal(QUrl)
    scroll_detected = pyqtSignal(QPointF)

    def __init__(self, *args, **kwargs):
        super(MyMapViewPage, self).__init__(*args, **kwargs)
        self.channel = QWebChannel()
        self.scrollPositionChanged.connect(self.onScrollPos)

    def zoomChanged(self, value):
        self.setZoomFactor(value)

    def onScrollPos(self, qPointF):
        self.scroll_detected.emit(qPointF)

    def acceptNavigationRequest(self, qUrl, QWebEnginePage_NavigationType, abool):
        if QWebEnginePage_NavigationType == QWebEnginePage.NavigationTypeLinkClicked:
            self.link_clicked.emit(qUrl)
            return False
        return super(MyMapViewPage, self).acceptNavigationRequest(qUrl, QWebEnginePage_NavigationType, abool)


class PanningWebView(QWidget):
# class PanningWebView(QWebEngineView):
    zoom_factor = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pressed = False
        self._parent = parent
        self._page = MyMapViewPage()
        self.view = QWebEngineView()
        self.view.setPage(self.page())
        self.mapView = self._page
        self.vl = QVBoxLayout()
        self.vl.addWidget(self.view)
        self.setLayout(self.vl)

    def setZoomFactor(self, value):
        return self.page().setZoomFactor(value)

    def zoomFactor(self):
        return self.page().zoomFactor()

    # imitate QWebEngineView
    def page(self):
        return self._page

    # not seemed to be triggered ever
    def eventFilter(self, a0: 'QObject', a1: 'QEvent') -> bool:
        print("{} {} {} {}".format(a0, self, a0.parent(), a1.type()))
        # print(a0.children())
        if  a0 == self:
        # if self.mapView and a0 == self.mapView:
            if a1.type() == QEvent.MouseMove:
                return self.mouseMoveEventHandler(a1)
            if a1.type() == QEvent.MouseButtonPress:
                return self.mousePressEventHandler(a1)
            if a1.type() == QEvent.MouseButtonRelease:
                return self.mouseReleaseEventHandler(a1)
        return False

    def setHtml(self, p_str, baseUrl=None, *args, **kwargs):
        self.page().setHtml(p_str, baseUrl, args, kwargs)

    @QtCore.pyqtSlot(bool)
    def _loadFinished(self, ok):
        if not ok:
            return
        # if self.mapView is None:
        #     self.mapView = self.page()
        #     for child in self.children():
        #         if child == self.mapView:
        #             self.installEventFilter(child)
        if self.initialMapPosition is None:
            scrollPosition = QPointF(self.mapView.scrollPosition())
        else:
            scrollPosition = self.initialMapPosition
        self.mapView.runJavaScript(str("window.scrollTo({}, {});".
                                              format(scrollPosition.x(),scrollPosition.y())))
        self.initialMapPosition = self.mapView.scrollPosition()
        if scrollPosition.x() == 0 and scrollPosition.y() == 0:
            self.initialMapPosition = None

    def mousePressEventHandler(self, mouseEvent):
        pos = mouseEvent.pos()
        if self.pointInScroller(pos, Qt.Vertical) or self.pointInScroller(pos, Qt.Horizontal):
            self.clickedInScrollBar = True
            self.scroll_detected.emit()
        else:
            if self.ignored.count(mouseEvent):
                self.ignored.remove(mouseEvent)
                return QActionEvent.MouseButtonPress(self, mouseEvent)
                # return QWebView.mousePressEvent(self, mouseEvent)

            if not self.pressed and not self.scrolling and mouseEvent.modifiers() == Qt.NoModifier:
                if mouseEvent.buttons() == Qt.LeftButton:
                    self.pressed = True
                    self.scrolling = False
                    self.handIsClosed = False
                    QCoreApplication.setOverrideCursor(Qt.OpenHandCursor)

                    self.position = mouseEvent.pos()
                    frame = self.page().mainFrame()
                    xTuple = frame.evaluateJavaScript("window.scrollX").toInt()
                    yTuple = frame.evaluateJavaScript("window.scrollY").toInt()
                    self.offset = Qt.QPoint(xTuple[0], yTuple[0])
                    return

        # return QWebView.mousePressEvent(self, mouseEvent)
        return QActionEvent.MouseButtonPress(self, mouseEvent)


    def mouseReleaseEventHandler(self, mouseEvent):
        super(PanningWebView, self).mouseReleaseEvent(mouseEvent)
        if self.clickedInScrollBar:
            self.clickedInScrollBar = False
        else:
            if self.ignored.count(mouseEvent):
                self.ignored.remove(mouseEvent)
                return QActionEvent.MouseButtonPress(self, mouseEvent)
                # return QWebView.mousePressEvent(self, mouseEvent)

            if self.scrolling:
                self.pressed = False
                self.scrolling = False
                self.handIsClosed = False
                QCoreApplication.restoreOverrideCursor()
                return

            if self.pressed:
                self.pressed = False
                self.scrolling = False
                self.handIsClosed = False
                QCoreApplication.restoreOverrideCursor()

                event1 = QMouseEvent(QActionEvent.MouseButtonPress, self.position, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                # event1 = QMouseEvent(QEvent.MouseButtonPress, self.position, QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
                event2 = QMouseEvent(mouseEvent)
                self.ignored.append(event1)
                self.ignored.append(event2)
                QCoreApplication.postEvent(self, event1)
                QCoreApplication.postEvent(self, event2)
                return
        return QCoreApplication.mouseReleaseEvent(self, mouseEvent)


    def mouseMoveEventHandler(self, mouseEvent):
        super(PanningWebView, self).mouseMoveEvent(mouseEvent)

        if not self.clickedInScrollBar:
            if self.scrolling:
                if not self.handIsClosed:
                    QCoreApplication.restoreOverrideCursor()
                    QCoreApplication.setOverrideCursor(Qt.ClosedHandCursor)
                    self.handIsClosed = True
                delta = mouseEvent.pos() - self.position
                p = self.offset - delta
                frame = self.page().mainFrame()
                frame.evaluateJavaScript(str("window.scrollTo(%1, %2);").arg(p.x()).arg(p.y()));
                return

            if self.pressed:
                self.pressed = False
                self.scrolling = True
                self.scroll_detected.emit()
                return
        # return QWebView.mouseMoveEvent(self, mouseEvent)
        # return QActionEvent.MouseButtonPress(self, mouseEvent)


    def pointInScroller(self, position, orientation):
        rect = self.page().geometryChangeRequested(orientation)
        # rect = self.page().mainFrame.scrollBarGeometry(orientation)
        # rect = self.page().mainFrame().scrollBarGeometry(orientation)
        leftTop = self.mapToGlobal(Qt.QPoint(rect.left(), rect.top()))
        rightBottom = self.mapToGlobal(Qt.QPoint(rect.right(), rect.bottom()))
        globalRect = Qt.QRect(leftTop.x(), leftTop.y(), rightBottom.x(), rightBottom.y())
        return globalRect.contains(self.mapToGlobal(position))

