'''
Created on Jun 6, 2024

@author: boogie
'''
from urllib import parse
import lxml.html
import os

from livearchive import model
from livearchive import entry


def human2bytes(s):
    s = s.strip()
    units = ["iB"]
    replaces = [" ", ","]
    for unit in units:
        if s.endswith(unit):
            s = s[:-len(unit)].strip()
    for replace in replaces:
        s = s.replace(replace, "")
    if s is None:
        return 0
    try:
        return int(s)
    except ValueError:
        symbols = 'BKMGTPEZY'
        letter = s[-1:].strip().upper()
        num = float(s[:-1])
        prefix = {symbols[0]: 1}
        for i, s in enumerate(symbols[1:]):
            prefix[s] = 1 << (i+1)*10
        return int(num * prefix[letter])


class TheEye(model.Scraper):
    base = "https://the-eye.eu/public/"
    name = "The Eye"
    xpath_link = ".//pre/a[position()>1]"

    def stat(self, path):
        u = self.base + parse.quote(path)
        head = self.cache.request(u, ishead=True)
        if head:
            paths = [x for x in path.split(os.path.sep) if x != ""]
            e = entry.Entry()
            e.set(name=paths[-1] if len(paths) else self.name)
            ctype = head.headers.get('Content-Type', 'text/html')
            if 'text/html' in ctype:
                e.set(isfolder=True)
            else:
                e.set(filesize=int(head.headers.get('Content-length', 0)), url=u)
            return e

    def link2addr(self, link):
        return link.get("href")

    def link2size(self, link):
        return link.tail.split(" ")[-1]

    def iterlinks(self, html):
        for link in html.xpath(self.xpath_link):
            e = entry.Entry()
            name = parse.unquote(self.link2addr(link))
            isfolder = False
            url = None
            filesize = 0
            if name.endswith("/"):
                isfolder = True
                name = name[:-1]
            if not isfolder:
                filesize = human2bytes(self.link2size(link))
            e.set(name=name, isfolder=isfolder, url=url, filesize=filesize, inaccurate_size=True)
            yield e

    def iterentries(self, path):
        u = self.base + path + "/"
        resp = self.cache.request(u)
        html = lxml.html.fromstring(resp.content)
        for e in self.iterlinks(html):
            yield e
