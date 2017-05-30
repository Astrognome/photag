import os
import sys

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class Directory(Base):
    __tablename__ = 'directory'

    id = Column(Integer, primary_key=True)
    path = Column(String(500), nullable=False)
    parent_id = Column(Integer, ForeignKey('directory.id'))
    parent = relationship('Directory', remote_side=[id], backref='children')
    medias = relationship('Media', backref="directory")

    def getFullPath(self):
        path = self.path
        parent = self.parent
        while parent:
            path = os.path.join(parent.path, path)
            parent = parent.parent
        return path

tag_association = Table('tag_association', Base.metadata,
                        Column('media_id', Integer, ForeignKey('media.id')),
                        Column('tag_id', Integer, ForeignKey('tag.id'))
                        )

class Media(Base):
    __tablename__ = 'media'

    id = Column(Integer, primary_key=True)
    file_name = Column(String(200), nullable=False)
    directory_id = Column(Integer, ForeignKey('directory.id'))
    tags = relationship("Tag", secondary=tag_association, back_populates="medias")

    def getFullPath(self):
        return os.path.join(self.directory.getFullPath(), self.file_name)

class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey('tag.id'))
    parent = relationship('Tag', remote_side=[id], backref='children')
    medias = relationship("Media", secondary=tag_association, back_populates="tags")

### Querys

class Query(object):
    def __init__(self, name=None):
        if not name:
            self.name = "new query"
        else:
            self.name = name
        self.queries = []
        self.medias = []

    def execute(self):
        pass

class DirQuery(Query):
    def __init__(self, directory):
        super().__init__(directory.path)
        self.directory = directory

    def execute(self):
        children = self.directory.children
        for child in children:
            self.queries.append(DirQuery(child))
        self.medias = self.directory.medias

class TagQuery(Query):
    def __init__(self, tag):
        super().__init__(tag.name)
        self.tag = tag

    def execute(self):
        children = self.tag.children
        for child in children:
            self.queries.append(TagQuery(child))
        self.medias = self.tag.medias

class MediaWithTagsQuery(Query):
    def __init__(self, tags, db):
        super().__init__("MediWithTagsQuery")
        self.tags = tags
        self.db = db

    def execute(self):
        print(self.tags)
        media_query = self.db.session.query(Media).filter(Media.tags.contains(self.tags[0]))
        for tag in self.tags[1:]:
            media_query = media_query.filter(Media.tags.contains(tag))
        self.medias = media_query.all()

class WholeTreeQuery(Query):
    def __init__(self, db):
        super().__init__("WholeTreeQuery")
        self.roots = db.getRootDirs()

    def execute(self):
        for root in self.roots:
            self.queries.append(DirQuery(root))

class AllMediaFlatQuery(Query):
    def __init__(self, db):
        super().__init__("AllMediaFlatQuery")
        self.session = db.session

    def execute(self):
        self.medias = self.session.query(Media).all()

class TagTreeQuery(Query):
    def __init__(self, db):
        super().__init__("TagTreeQuery")
        self.root_tags = db.session.query(Tag).filter(Tag.parent == None).all()

    def execute(self):
        for root in self.root_tags:
            self.queries.append(TagQuery(root))

class PhotagDB():
    def __init__(self):
        self.engine = create_engine("sqlite:///photag.db")
        if not os.path.isfile("photag.db"):
            Base.metadata.create_all(self.engine)

        Base.metadata.bind = self.engine
        self.db_session = sessionmaker(bind=self.engine)

        self.session = self.db_session()

    def getRootDirs(self):
        session = self.session
        dirs = session.query(Directory).filter(Directory.parent == None).all()
        return dirs

    def getDirChildren(self, base_dir):
        session = self.db_session()
        dirs = session.query(Directory).filter(Directory.parent == base_dir).all()
        return dirs

    def addDir(self, dir_path, parent=None):
        session = self.session
        new_dir = session.query(Directory).filter(Directory.path == dir_path).filter(Directory.parent == parent).first()
        if not new_dir:
            new_dir = Directory(path=dir_path, parent=parent)
            session.add(new_dir)
            session.commit()
        return new_dir

    def remDir(self, dir):
        subDirs = dir.children
        for child in children:
            remDir(dir)
        medias = dir.medias
        for media in medias:
            self.session.delete(media)
        self.session.delete(dir)

    def addMedia(self, filename, directory):
        session = self.session
        new_media = session.query(Media).filter(Media.directory == directory).filter(Media.file_name == filename).first()
        if not new_media:
            new_media = Media(file_name=filename, directory=directory)
            session.add(new_media)
            session.commit()
        return new_media

    def walkDir(self, dir_to_walk):
        full_path = dir_to_walk.getFullPath()
        listing = os.listdir(full_path)
        for item in listing:
            if os.path.isdir(os.path.join(full_path, item)):
                self.walkDir(self.addDir(item, dir_to_walk))
            elif os.path.isfile(os.path.join(full_path, item)):
                self.addMedia(item, dir_to_walk)

    def walkAllRoots(self):
        session = self.db_session()
        root_dirs = self.getRootDirs()
        for root_dir in root_dirs:
            self.walkDir(root_dir)

    # return a query based on a string
    def stringQuery(self, query_string):
        if query_string == "TAG_TREE":
            return TagTreeQuery(self)
        elif query_string == "WHOLE_TREE" or query_string == "":
            return WholeTreeQuery(self)
        splits = query_string.split(';')
        for split in splits:
            if split.startswith("HAS_TAGS"):
                tags = split.split(' ')[1:]
                tag_obs = []
                for tag in tags:
                    tag_obs.append(self.session.query(Tag).filter(Tag.name == tag).first())
                return MediaWithTagsQuery(tag_obs, self)

