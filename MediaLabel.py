from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap

class MediaLabel(QLabel):
    def __init__(self, parent):
        super(MediaLabel,self).__init__(parent)

        self._pixmap = QPixmap()
        self.setScaledContents(False)

    def heightForWidth(self, width):
        if self._pixmap.isNull():
            return self.height()
        return (self._pixmap.height()*width)/self._pixmap.width()

    def sizeHint(self):
        w = self.width()
        return QSize(w, self.heightForWidth(w))

    def scaledPixmap(self):
        return self._pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def setSPixmap(self, pixmap):
        self._pixmap = pixmap
        self.setPixmap(self.scaledPixmap())

    def resizeEvent(self, event):
        if not self._pixmap.isNull():
            self.setPixmap(self.scaledPixmap())
