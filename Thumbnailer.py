# A thumbnailer with cache using QT and sqlite
# TODO
# Have it delete thumbnails when requesting an image that no longer exists

import os
import sqlite3
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice

class Thumbnailer():
    def __init__(self, db_filename = "thumbnails.db"):
        db_exists = False
        if os.path.exists(db_filename):
            db_exists = True

        self.conn = sqlite3.connect(db_filename)
        if not db_exists:
            self.conn.execute('''CREATE TABLE thumbnails
            (id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            dim INTEGER NOT NULL,
            timestamp INT NOT NULL,
            pix BLOB NOT NULL
            );''')

    def requestThumbnail(self, filename, size = 100, commit = True):
        # check if thumbnail already exists in db
        c = self.conn.cursor()
        c.execute("SELECT * FROM thumbnails WHERE filename=? AND dim=? ", (filename,size))
        row = c.fetchone()
        if row:
            pix_data = row[4]
            image = QImage()
            ba = QByteArray(bytes(pix_data))
            image.loadFromData(ba)
            return image

        # if not, make it, store it, return it
        image = QImage(filename).scaledToHeight(size)

        #write image to a buffer
        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.WriteOnly)
        image.save(buf, 'JPEG')

        #bytes(buf.data())
        #insert the thumbnail into the db
        c.execute("INSERT INTO thumbnails (filename, dim, timestamp, pix) values (?, ?, ?, ?)", (filename, size, 0, bytes(buf.data())))
        if commit:
            self.conn.commit()

        return image
        

if __name__ == "__main__":
    #test stuff
    thumbnailer = Thumbnailer("thumbtest.db")
    thumbnailer.requestThumbnail("test.jpg").save("thumb.jpg")

