#!/usr/bin/env python

#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.
#
from liblivearchive import cache
from liblivearchive import entry
from liblivearchive import model
from liblivearchive import log
from liblivearchive import scrapers
import os
import stat
import errno
import argparse
import fuse
import sys
import threading


IGNORE_PATHS = [".hidden", ".trash", ".trash-1000", "bdmv", ".xdg-volume-info", ".autorun.inf", "autorun.inf", ".sh_thumbnails"]


class LiveArchiveFS:
    def __init__(self, cachepath, cachesize, cachetime, debug=False):
        self.debug = debug
        if self.debug:
            log.setlevel(log.debug)
        self.cache = cache.Cache(cachepath, cachesize, cachetime)
        self.scrapers = scrapers.getscrapers(self.cache)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cache.close()
        return

    def getscraper(self, path):
        if path:
            paths = [x for x in path.split(os.path.sep) if x != ""]
            if len(paths):
                for scraper in self.scrapers:
                    if paths[0] == scraper.name:
                        return scraper, os.path.sep.join(paths[1:])
        return None, None

    def getattr(self, path):
        e = entry.Entry.get(path)
        if not e:
            scraper, scraperpath = self.getscraper(path)
            if scraper:
                e = scraper.stat(scraperpath)
            if not e:
                if path.split(os.path.sep)[-1].lower() not in IGNORE_PATHS:
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


def main():
    parser = argparse.ArgumentParser(prog='LiveArchive',
                                     description='This tool binds online archiving services to vitual folders on your filesystem')
    parser.add_argument('mountpath')
    parser.add_argument('-cp', '--cache-path', default=cache.CACHEPATH)
    parser.add_argument('-ct', '--cache-time', default=cache.CACHEAGE / (60 * 60 * 24))
    parser.add_argument('-cs', '--cache-size', default=cache.CACHESIZE / (1024 * 1024))
    parser.add_argument('-d', '--debug', action="store_true")
    parser.add_argument('-df', '--debug-fuse', action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.mountpath):
        log.logger.error(f"Mount path {args.mountpath} does not exist")
        sys.exit(-1)
    if not os.path.exists(args.cache_path):
        if args.cache_path == cache.CACHEPATH:
            os.makedirs(args.cache_path, exist_ok=True)
        else:
            log.logger.error(f"Cache path {args.cache_path} does not exist")
            sys.exit(-1)

    with LiveArchiveFS(args.cache_path, args.cache_size * 1024 * 1024, args.cache_time * 60 * 60 * 24, args.debug) as server:
        fuseargs = ["", args.mountpath, "-f", "-o", "auto_unmount"]
        if args.debug_fuse:
            fuseargs.append("-d")
        t = threading.Thread(target=fuse.main, kwargs={"multithreaded": 1,
                                                       "fuse_args": fuseargs,
                                                       "getattr": fuse.ErrnoWrapper(server.getattr),
                                                       "open": fuse.ErrnoWrapper(server.open),
                                                       "readdir": fuse.ErrnoWrapper(server.readdir),
                                                       "read": fuse.ErrnoWrapper(server.read)}, daemon=True)
        # libfuse is handling their own ctrl+c signals, and blocks exit, therefore running it in thread
        # so we can catch signals from the main thread. This is a workaround to exit gracefully
        t.start()
        t.join()


if __name__ == '__main__':
    main()
