'''
Created on Jun 6, 2024

@author: boogie
'''
import os
import slugify
import re

from liblivearchive import model
from liblivearchive import entry
from liblivearchive import log


roots = ["movies", "image", "texts", "audio", "software"]

FILELIST = "Files"


class PathSpec:
    def __init__(self, path):
        self.name = None
        self.mediatype = None
        self.uid = None
        self.filelist = False
        self.file = False
        paths = [x for x in path.split(os.path.sep) if x != ""]
        if len(paths):
            m = re.search("(.+)\s\-\s(.+)\s\((.+?)\)", paths[-1])
            if len(paths) > 1 and m is None:
                pre_m = re.search("(.+)\s\-\s(.+)\s\((.+?)\)", paths[-2])
                if pre_m is not None:
                    m = pre_m
                    # FIX-ME: if there is a file with the name defined in FILELIST our logic will fail.
                    if paths[-1] == FILELIST:
                        self.filelist = True
                    else:
                        self.file = True
                        self.name = paths[-1]
            if m:
                self.name = self.name or m.group(1)
                self.mediatype = m.group(2)
                self.uid = m.group(3)


class InternetArchive(model.Scraper):
    name = "Internet Archive"
    search = "https://archive.org/services/search/v1/scrape"

    def geduid(self, path):
        return re.search("\(\)", path).group(1)

    def scrape(self, search, criteria):
        cursor = ""
        count = 0
        while True:
            u = f"{search}{criteria}{cursor}"
            js = self.cache.request(u, json=True)
            if not js:
                break
            for col in js.get("items", []):
                count += 1
                title = col.get('title', "unknown")
                if isinstance(title, list):
                    title = title[0]
                yield self.direntry(title, col['identifier'], col.get('mediatype'))
            cur = js.get("cursor")
            if cur:
                cursor = f"&cursor={cur}"
            else:
                break
        log.logger.debug(f"returned {count} entry(ies) for {criteria}")

    def parseuid(self, path):
        m = re.search("\((.+?)\)", path)
        if m:
            return m.group(1)

    def stat(self, path):
        spec = PathSpec(path)
        if spec.uid:
            entries = list(self.scrape(f"{self.search}?&q=identifier:", spec.uid))
            if entries:
                if not spec.file:
                    return entries[0]
                else:
                    for item in self.getfiles(spec.uid):
                        if item["name"] == spec.name:
                            return self.fileentry(item, spec.uid)

    def getfiles(self, uid):
        u = f"https://archive.org/metadata/{uid}"
        js = self.cache.request(u, json=True)
        return js.get("files", [])

    def direntry(self, name, uid, mediatype):
        e = entry.Entry()
        sluggy = slugify.slugify(name, separator=' ', lowercase=False)
        name = f"{sluggy} - {mediatype} ({uid})"
        e.set(name=name, isfolder=True, url=mediatype)
        return e

    def fileentry(self, fitem, uid):
        name = fitem['name']
        url = f"https://archive.org/download/{uid}/{name}"
        filesize = int(fitem.get('size', 64))
        e = entry.Entry()
        e.set(name=name, isfolder=False, url=url, filesize=filesize)
        return e

    def iterentries(self, path):
        spec = PathSpec(path)
        if not spec.uid:
            for root in roots:
                e = entry.Entry()
                e.set(name=f"{root} - collection ({root})", isfolder=True)
                yield e
        else:
            if not spec.filelist:
                dircount = 0
                for e in self.scrape(f"{self.search}?fields=title,mediatype&q=mediatype:collection collection:", spec.uid):
                    dircount += 1
                    yield e
                if spec.mediatype != "collection":
                    for fitem in self.getfiles(spec.uid):
                        yield self.fileentry(fitem, spec.uid)
                elif not dircount:
                    for e in self.scrape(f"{self.search}?fields=title,mediatype&q=collection:", spec.uid):
                        if e.url != "collection":
                            yield e
                else:
                    e = entry.Entry()
                    e.set("Files", isfolder=True)
                    yield e
            elif spec.filelist:
                # TODO: is there a better way to filter out collections when scraping?
                for e in self.scrape(f"{self.search}?fields=title,mediatype&q=collection:", spec.uid):
                    if e.url != "collection":
                        yield e
