'''
Created on Jun 6, 2024

@author: boogie
'''
from urllib import parse
import lxml.html
import os

from liblivearchive import model
from liblivearchive import entry


class TheEye(model.Scraper):
    base = "https://beta.the-eye.eu/public/"
    name = "The Eye"

    def stat(self, path):
        u = self.base + path
        head = self.cache.request(u, ishead=True)
        if head:
            paths = [x for x in path.split(os.path.sep) if x != ""]
            e = entry.Entry()
            e.set(name=paths[-1])
            ctype = head.get('Content-Type')
            if 'text/html' in ctype:
                e.set(isfolder=True)
            else:
                e.set(filesize=int(head.get('Content-length', 64)), url=u)
            return e

    def iterentries(self, path):
        u = self.base + path + "/"
        page = self.cache.request(u)
        html = lxml.html.fromstring(page)
        for link in html.xpath("..//td[@class='filename']/a[@class='overflow']/@href"):
            e = entry.Entry()
            name = parse.unquote(link.encode().decode())
            isfolder = False
            filesize = None
            url = None
            if name.endswith("/"):
                isfolder = True
                name = name[:-1]
            if not isfolder:
                url = u + link
                headers = {"Accept-Encoding": "identity"}
                head = self.cache.request(url, headers=headers, ishead=True)
                filesize = int(head.get('Content-length', 64))
            e.set(name=name, isfolder=isfolder, url=url, filesize=filesize)
            yield e
