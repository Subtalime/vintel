
from PyQt5.QtGui import *
from PyQt5.QtCore import QCoreApplication, Qt, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView


class PanningWebView(QWebEngineView):
    scroll_detected = pyqtSignal()

    def __init__(self, parent=None):
        # super(PanningWebView).__init__(self)
        super(PanningWebView, self).__init__()
        self.pressed = False
        self.scrolling = False
        self.ignored = []
        self.position = None
        self.offset = 0
        self.handIsClosed = False
        self.clickedInScrollBar = False


    def mousePressEvent(self, mouseEvent):
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


    def mouseReleaseEvent(self, mouseEvent):
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


    def mouseMoveEvent(self, mouseEvent):
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
        return QActionEvent.MouseButtonPress(self, mouseEvent)


    def pointInScroller(self, position, orientation):
        rect = self.page().mainFrame().scrollBarGeometry(orientation)
        leftTop = self.mapToGlobal(Qt.QPoint(rect.left(), rect.top()))
        rightBottom = self.mapToGlobal(Qt.QPoint(rect.right(), rect.bottom()))
        globalRect = Qt.QRect(leftTop.x(), leftTop.y(), rightBottom.x(), rightBottom.y())
        return globalRect.contains(self.mapToGlobal(position))
