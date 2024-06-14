'''
Created on Jun 7, 2024

@author: boogie
'''
import threading
from livearchive import log


class Entry:
    entries = {}

    def __repr__(self):
        return self.path

    def __init__(self, path=None, multi=False):
        self.path = path
        if self.path not in self.entries:
            self.entries[self.path] = self
        self.lock = threading.Lock()
        self.multi = multi
        self.name = None
        self.isfolder = None
        self.filesize = 0
        self.url = None
        self.cursor = 0

    @staticmethod
    def update(entry):
        cacheentry = Entry.entries.get(entry.path)
        if cacheentry:
            log.logger.debug(f"Updating {cacheentry}")
            cacheentry.set(entry.name, entry.isfolder,
                           entry.filesize or cacheentry.filesize,
                           entry.url, entry.cursor)
        else:
            log.logger.debug(f"Adding {entry}")
            Entry.entries[entry.path] = entry

    @staticmethod
    def get(path):
        cached = Entry.entries.get(path)
        return cached

    def set(self, name=None, isfolder=None, filesize=None, url=None, cursor=None, path=None):
        self.name = name if name is not None else self.name
        self.isfolder = isfolder if isfolder is not None else self.isfolder
        self.filesize = filesize if filesize is not None else self.filesize
        self.url = url if url is not None else self.url
        self.cursor = cursor if cursor is not None else self.cursor
        self.path = path if path is not None else self.path

    def __enter__(self):
        instance = self.entries.get(self.path, self)
        if not self.multi:
            log.logger.debug(f"Locked {instance}")
            instance.lock.acquire()
        return instance

    def __exit__(self, exc_type, exc_val, exc_tb):
        instance = self.entries.get(self.path, self)
        if not self.multi:
            log.logger.debug(f"Unocked {instance}")
            instance.lock.release()
        return


root = Entry("/")
root.isfolder = True
Entry.entries["/"] = root
