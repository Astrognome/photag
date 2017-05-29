
from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex

from Database import Directory, Media, Query

class ImageViewModel(QAbstractItemModel):
    def __init__(self, query):
        QAbstractItemModel.__init__(self)
        self._root = ImageViewNode(None)
        self.setQuery(query)

    def rowCount(self, in_index):
        if in_index.isValid():
            return in_index.internalPointer().childCount()
        return self._root.childCount()

    def columnCount(self, in_index):
        return 1

    def addChild(self, in_node, in_parent):
        if not in_parent or not in_parent.isValid():
            parent = self._root
        else:
            parent = in_parent.internalPointer()
        parent.addChild(in_node)

    def index(self, in_row, in_column, in_parent=None):
        if not in_parent or not in_parent.isValid():
            parent = self._root
        else:
            parent = in_parent.internalPointer()
        if not QAbstractItemModel.hasIndex(self, in_row, in_column, in_parent):
            return QModelIndex()

        child = parent.child(in_row)
        if child:
            return QAbstractItemModel.createIndex(self, in_row, in_column, child)
        else:
            return QModelIndex()

    def parent(self, in_index):
        if in_index.isValid():
            p = in_index.internalPointer().parent()
            if p:
                return QAbstractItemModel.createIndex(self, p.row(),0,p)
        return QModelIndex()

    def columnCount(self, in_index):
        if in_index.isValid():
            return in_index.internalPointer().columnCount()
        return self._root.columnCount()

    def data(self, in_index, role):
        if not in_index.isValid():
            return None
        node = in_index.internalPointer()
        if role == Qt.DisplayRole:
            return node.data(in_index.column())
        return None

    def setQuery(self, query):
        self.reset()
        self.walkQueryAsNodes(self._root, query)

    def reset(self):
        super().beginResetModel()
        self._root._children = []
        super().endResetModel()

    # functions for things

    def walkQueryAsNodes(self, p_node, query):
        query.execute()
        children = query.queries 
        for child in children:
            new_node = ImageViewNode(child.name)

            p_node.addChild(new_node)
            self.walkQueryAsNodes(new_node, child)

        medias = query.medias
        for media in medias:
            new_node = ImageViewNode(media.file_name)
            new_node.setMedia(media)

            p_node.addChild(new_node)

class ImageViewNode(object):
    def __init__(self, in_data):
        self._data = in_data
        if type(in_data) == tuple:
            self._data = list(in_data)
        if type(in_data) == str or not hasattr(in_data, '__getitem__'):
            self._data = [in_data]

        self._columncount = len(self._data)
        self._children = []
        self._parent = None
        self._row = 0

        self.media = None

    def data(self, in_column):
        if in_column >= 0 and in_column < len(self._data):
            return self._data[in_column]

    def columnCount(self):
        return self._columncount

    def childCount(self):
        return len(self._children)

    def child(self, in_row):
        if in_row >= 0 and in_row < self.childCount():
            return self._children[in_row]

    def parent(self):
        return self._parent

    def row(self):
        return self._row

    def childCount(self):
        return len(self._children)

    def addChild(self, in_child):
        in_child._parent = self
        in_child._row = len(self._children)
        self._children.append(in_child)
        self._columncount = max(in_child.columnCount(), self._columncount)

    def setMedia(self, media):
        self.media = media

