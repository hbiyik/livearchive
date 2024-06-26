'''
Created on Jun 7, 2024

@author: boogie
'''
import requests
import os
import hashlib
import pickle
import time

from livearchive import log


class Cache:
    session = requests.Session()

    def __init__(self, path, maxsize, maxage):
        self.maxsize = maxsize
        self.maxage = maxage
        self.cachepath = path
        self.tidytime = 60
        self.indexfile = os.path.join(self.cachepath, "index.pickle")
        os.makedirs(self.cachepath, exist_ok=True)
        if not os.path.exists(self.indexfile):
            self.index = {}
            self.index["size"] = 0
        else:
            with open(self.indexfile, "rb") as fp:
                self.index = pickle.load(fp)

    def close(self):
        with open(self.indexfile, "wb") as fp:
            pickle.dump(self.index, fp)
            log.logger.debug(f"Cache saved at {self.cachepath}, size={self.index['size']}")

    def key(self, url, headers, ishead, json):
        hkey = ""
        if headers:
            for k in sorted(headers):
                hkey += headers[k].lower().strip()
        return hashlib.md5((str(json) + str(ishead) + hkey + url).encode()).hexdigest()

    def add(self, url, headers, data, ishead, json):
        key = self.key(url, headers, ishead, json)
        if key not in self.index:
            log.logger.debug(f"Cache added for {url}")
            data = pickle.dumps(data)
            with open(os.path.join(self.cachepath, key), "wb") as f:
                f.write(data)
            size = len(data)
            self.index[key] = [time.time(), size]
            self.index["size"] += size
            return True
        return False

    def get(self, url, headers, ishead=False, json=None):
        key = self.key(url, headers, ishead, json)
        if key in self.index:
            with open(os.path.join(self.cachepath, key), "rb") as fp:
                data = fp.read()
            return pickle.loads(data)
        return None

    def tidy(self):
        lookup = []
        for key in self.index:
            if key == "size":
                continue
            cachetime, cachesize = self.index[key]
            lookup.append([cachetime, cachesize, key])

        size = 0
        cleaned = 0
        for cachetime, cachesize, key in sorted(lookup, reverse=True):
            size += cachesize
            lifetime = time.time() - cachetime
            if lifetime >= self.maxage or size >= self.maxsize:
                cleaned += cachesize
                self.index.pop(key)
                os.remove(os.path.join(self.cachepath, key))
                log.logger.debug(f"Cleaned {cachesize} bytes")
        self.index["size"] = size - cleaned
        if cleaned:
            log.logger.debug(f"Total Cleaned {cleaned} bytes")

    def request(self, url, headers=None, json=None, ishead=False):
        self.tidy()
        cache = self.get(url, headers, ishead, json)
        if cache:
            return cache
        cb = Cache.session.head if ishead else Cache.session.get
        log.logger.debug(f"Http requesting {url}, ishead={ishead}")
        resp = cb(url, headers=headers, json=json, allow_redirects=True)
        if resp.status_code in [200, 206]:
            self.add(url, headers, resp, ishead, json)
            return resp
        else:
            return None
