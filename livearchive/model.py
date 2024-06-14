'''
Created on Jun 7, 2024

@author: boogie
'''
import fuse


class Entry:
    def __init__(self, txt, isfolder=None):
        self.txt = txt
        self.isfolder = isfolder or self.txt.endswith("/")
        self.name = self.txt[:-1] if self.isfolder else self.txt
        self.filesize = 64
        self.url = None
        self.cursor = 0


class Stat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


class Scraper:
    name = None

    def __init__(self, cache):
        self.cache = cache

    def read(self, entry, size):
        start = entry.cursor
        end = start + size - 1
        headers = {"Range": f"bytes={start}-{end}"}
        return self.cache.request(entry.url, headers=headers).content

    def iterentries(self, path):
        yield

    def stat(self, path):
        return
