'''
Created on Jun 7, 2024

@author: boogie
'''

from livearchive import cache
from livearchive import entry
from livearchive import model
from livearchive import log
from livearchive import scrapers

import stat
import errno
import os
import fuse
import signal
import sys


__version__ = "0.1"
IGNORE_PATHS = [".hidden", ".trash", ".trash-1000", "bdmv", ".xdg-volume-info", ".autorun.inf", "autorun.inf", ".sh_thumbnails"]
CACHEPATH = os.path.join(os.path.expanduser('~'), ".livearchive", "cache")
MOUNTPATH = os.path.join(os.path.expanduser('~'), ".livearchive", "livearchive")
CACHESIZE = 1024 * 1024 * 100
CACHEAGE = 60 * 60 * 6


class LiveArchiveFS:
    def __init__(self, cachepath=CACHEPATH, cachesize=CACHESIZE, cachetime=CACHEAGE, debug=False):
        self.debug = debug
        if self.debug:
            log.setlevel(log.debug)
        self.cache = cache.Cache(cachepath, cachesize, cachetime)
        self.scrapers = scrapers.getscrapers(self.cache)
        signal.signal(signal.SIGTERM, self.signal)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cache.close()
        return

    def signal(self, *args, **kwargs):
        raise(KeyboardInterrupt)

    def getscraper(self, path):
        if path:
            paths = [x for x in path.split(os.path.sep) if x != ""]
            if len(paths):
                for scraper in self.scrapers:
                    if paths[0] == scraper.name:
                        return scraper, os.path.sep.join(paths[1:])
        return None, None

    def getattr(self, path):
        ignored = path.split(os.path.sep)[-1].lower() in IGNORE_PATHS
        if ignored:
            return -errno.ENOENT
        e = entry.Entry.get(path)
        scraper, scraperpath = self.getscraper(path)
        if not e:
            if scraper:
                e = scraper.stat(scraperpath)
            if not e:
                log.logger.warning(f"Tried to stat {path} but not found")
                return -errno.ENOENT
            else:
                log.logger.debug(f"Manual stat {path} found")
                e.set(path=path)
                entry.Entry.update(e)
        st = model.Stat()
        if e.isfolder:
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        else:
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = e.filesize
        return st

    def readdir(self, path, offset):
        if path == "/":
            for scraper in self.scrapers:
                with entry.Entry(path + scraper.name, multi=True) as e:
                    e.set(scraper.name, True)
                yield fuse.Direntry(e.name)
        else:
            scraper, scraperpath = self.getscraper(path)
            for e in scraper.iterentries(scraperpath):
                e.set(path=os.path.join(path, e.name))
                entry.Entry.update(e)
                yield fuse.Direntry(e.name)

    def open(self, path, flags):
        e = entry.Entry.get(path)
        if not e:
            log.logger.warning(f"Tried to open {path} but not found")
            return -errno.ENOENT
        scraper, scraperpath = self.getscraper(path)
        if e.inaccurate_size:
            e = scraper.stat(scraperpath)
            log.logger.debug(f"Manual stat {path} found")
            e.set(path=path)
            entry.Entry.update(e)
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            log.logger.warning(f"Tried to open {path} but flags {flags} are not proper")
            return -errno.EACCES
        e.cursor = 0
        log.logger.debug(f"Opened {path} with flags {flags}")

    def read(self, path, size, offset):
        e = entry.Entry.get(path)
        if not e:
            log.logger.warning(f"Tried to read {path} but not found")
            return -errno.ENOENT
        if offset:
            e.cursor = offset
        scraper, _ = self.getscraper(path)
        d = scraper.read(e, size)
        log.logger.debug(f"Read {path} - {e.cursor} - {size}")
        e.cursor += size
        return d
