import managerootsui

from PyQt5.QtWidgets import QWidget, QFileDialog

class ManageRootsInterface(QWidget, managerootsui.Ui_Form):
    def __init__(self, database, parent=None):
        super(ManageRootsInterface, self).__init__(parent)
        self.setupUi(self)
        self.db = database
        self.do_stuff()

    def add_root(self):
        new_dir = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        self.db.addDir(new_dir)

    def del_root(self):
        text = self.list.currentItem().text()
        self.db.remDir(self.db.session.query(Directory).filter(Directory.path == text).first())

    def do_stuff(self):
        roots = self.db.getRootDirs()
        for root in roots:
            self.list.addItem(root.path)

        self.add_button.clicked.connect(self.add_root)
        self.delete_button.clicked.connect(self.del_root)
