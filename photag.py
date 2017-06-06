#!/usr/bin/python

from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QLineEdit, QMenu
from PyQt5.QtGui import QImageReader, QImage, QPixmap
import sys

import maininterface
from managerootsinterface import ManageRootsInterface
from MediaLabel import MediaLabel
from ImageViewModel import ImageViewModel, ImageViewNode
from TagViewModel import TagViewModel, TagViewNode

from Database import PhotagDB, Directory, DirQuery, WholeTreeQuery, AllMediaFlatQuery, TagTreeQuery, Tag, Query


class MainInterface(QMainWindow, maininterface.Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainInterface, self).__init__(parent)
        self.setupUi(self)

class Photag():
    def __init__(self):
        pass


    def newTag(self, event):
        text, okay = QInputDialog.getText(None, "New Tag",
                                    "Tag: ", QLineEdit.Normal,
        )
        if okay:
            split = str.split(text,'.')
            last_tag = None
            for tag_name in split:
                new_tag = self.db.session.query(Tag).filter(Tag.name==tag_name).first()
                if not new_tag:
                    new_tag = Tag(name=tag_name, parent=last_tag)
                last_tag = new_tag
                self.db.session.add(new_tag)
                self.db.session.commit()
        self.form.tag_tree_view.model().reset()

    def tagCurrentSelected(self, index):
        node = index.internalPointer()
        selected = self.form.image_tree_view.selectionModel().selectedIndexes()
        for selection in selected:
            if selection.internalPointer().media:
                selection.internalPointer().media.tags.append(node.tag)
        self.db.session.commit()

    def updateMediaLabel(self, selected, old_selected):
        index = selected
        node = index.internalPointer()
        #print(node.media.getFullPath())
        if node.media:
            pm = QPixmap(node.media.getFullPath())
            self.form.media_label.setSPixmap(pm)

            # update tags in taglist
            taglist = self.form.current_tags_list
            taglist.clear()
            tags = node.media.tags
            for tag in tags:
                taglist.addItem(tag.name)

    def walkAllRoots(self):
        self.db.walkAllRoots()

    def enterQuery(self):
        new_query = self.db.stringQuery(self.form.query_bar.text())
        self.form.image_tree_view.model().setQuery(new_query)

    def manageRoots(self):
        self.manageRootsForm = ManageRootsInterface(self.db)
        self.manageRootsForm.show()

    def imageTreeContextMenu(self, point):
        index = self.form.image_tree_view.indexAt(point)
        if index.isValid():
            query = index.internalPointer().query
            #this node is a directory
            if query and type(query) == DirQuery:
                self.db.walkDir(query.directory)


    def main(self):
        self.app = QApplication(sys.argv)
        self.form = MainInterface()
        self.form.show()

        # db stuff
        self.db = PhotagDB()

        # context menu
        self.form.image_tree_view.customContextMenuRequested.connect(self.imageTreeContextMenu)

        baseQuery = WholeTreeQuery(self.db)
        self.form.image_tree_view.setModel(ImageViewModel(baseQuery))
        self.form.tag_tree_view.setModel(TagViewModel(self.db))

        self.form.image_tree_view.selectionModel().currentChanged.connect(self.updateMediaLabel)
        self.form.action_new_tag.triggered.connect(self.newTag)
        self.form.action_walk_roots.triggered.connect(self.walkAllRoots)
        self.form.tag_tree_view.doubleClicked.connect(self.tagCurrentSelected)
        self.form.query_bar.returnPressed.connect(self.enterQuery)

        self.form.action_manage_roots.triggered.connect(self.manageRoots)

        self.app.exec_()


if __name__ == '__main__':
    photag = Photag()
    photag.main()
