# A thumbnailer with cache using QT and sqlite
# TODO
# Have it delete thumbnails when requesting an image that no longer exists

import os
import sqlite3
import time
from collections import deque
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice, QObject, pyqtSignal
from Database import Media

class Thumbnailer(QObject):
    thumbnailFetched = pyqtSignal(QImage, str)
    def __init__(self, db_filename = "thumbnails.db", parent=None):
        super().__init__(parent)
        self.thumbsize = 100
        self.requestQueue = deque()

        db_exists = False
        if os.path.exists(db_filename):
            db_exists = True

        self.db_filename = db_filename
        self.conn = sqlite3.connect(db_filename)
        if not db_exists:
            self.conn.execute('''CREATE TABLE thumbnails
            (id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            dim INTEGER NOT NULL,
            timestamp INT NOT NULL,
            pix BLOB NOT NULL
            );''')

    def processRequests(self):
        while True:
            try:

                request = self.requestQueue.pop()
                filename = request.getFullPath()
                # check if thumbnail already exists in db
                c = sqlite3.connect(self.db_filename).cursor()
                c.execute("SELECT * FROM thumbnails WHERE filename=? AND dim=? ", (filename,self.thumbsize))
                row = c.fetchone()
                if row:
                    pix_data = row[4]
                    image = QImage()
                    ba = QByteArray(bytes(pix_data))
                    image.loadFromData(ba)
                    self.thumbnailFetched.emit(image,request.file_name)
                else:
                    # if not, make it, store it, return it
                    image = QImage(filename).scaledToHeight(self.thumbsize)

                    #write image to a buffer
                    ba = QByteArray()
                    buf = QBuffer(ba)
                    buf.open(QIODevice.WriteOnly)
                    image.save(buf, 'JPEG')

                    #bytes(buf.data())
                    #insert the thumbnail into the db
                    c.execute("INSERT INTO thumbnails (filename, dim, timestamp, pix) values (?, ?, ?, ?)", (filename, self.thumbsize, 0, bytes(buf.data())))

                    self.thumbnailFetched.emit(image,request.file_name)
            except IndexError:
                time.sleep(.25)

    def requestThumbnail(self, media):
        self.requestQueue.append(media)

    def cancelAllRequests(self):
        self.requestQueue.clear()

if __name__ == "__main__":
    #test stuff
    thumbnailer = Thumbnailer("thumbtest.db")
    thumbnailer.requestThumbnail("test.jpg").save("thumb.jpg")

