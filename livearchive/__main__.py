#!/usr/bin/env python

#    Copyright (C) 2006  Andrew Straw  <strawman@astraw.com>
#
#    This program can be distributed under the terms of the GNU LGPL.
#    See the file COPYING.

from livearchive import scrapers#
from livearchive import log
import livearchive

import os
import argparse
import fuse
import sys
import threading


def main():
    names = [x.name for x in scrapers.classes]
    parser = argparse.ArgumentParser(prog='LiveArchive',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=f"%(prog)s binds online archiving services ({', '.join(names)}) to vitual folders on your filesystem")
    parser.add_argument('-m', '--mount', default=livearchive.MOUNTPATH, help="path to mount directory")
    parser.add_argument('-cp', '--cache-path', default=livearchive.CACHEPATH, help="path to cache directory")
    parser.add_argument('-ct', '--cache-time', default=livearchive.CACHEAGE / (60 * 60 * 24), help="time in hours when the cached data will be invalid")
    parser.add_argument('-cs', '--cache-size', default=livearchive.CACHESIZE / (1024 * 1024), help="size in MB that the total cache will be")
    parser.add_argument('-d', '--debug', action="store_true", help="enable debug logging for the daemon")
    parser.add_argument('-df', '--debug-fuse', action="store_true", help="enable debug logging for underlying libfuse")
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {livearchive.__version__}')
    args = parser.parse_args()

    for cfg, default in [(args.mount, livearchive.MOUNTPATH), (args.cache_path, livearchive.CACHEPATH)]:
        if cfg == default:
            os.makedirs(cfg, exist_ok=True)
        elif not os.path.exists(cfg):
            log.logger.error(f"configured path {cfg} does not exist")
            sys.exit(-1)

    with livearchive.LiveArchiveFS(args.cache_path, args.cache_size * 1024 * 1024, args.cache_time * 60 * 60 * 24, args.debug) as server:
        fuseargs = ["", args.mount, "-f", "-o", "auto_unmount"]
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
