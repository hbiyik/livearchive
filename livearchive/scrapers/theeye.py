'''
Created on Jun 6, 2024

@author: boogie
'''
from urllib import parse
import lxml.html
import os

from livearchive import model
from livearchive import entry


class TheEye(model.Scraper):
    base = "https://beta.the-eye.eu/public/"
    name = "The Eye"
    regex = "..//td[@class='filename']/a[@class='overflow']/@href"

    def stat(self, path):
        u = self.base + parse.quote(path)
        head = self.cache.request(u, ishead=True)
        if head:
            paths = [x for x in path.split(os.path.sep) if x != ""]
            e = entry.Entry()
            e.set(name=paths[-1])
            ctype = head.headers.get('Content-Type', 'text/html')
            if 'text/html' in ctype:
                e.set(isfolder=True)
            else:
                e.set(filesize=int(head.headers.get('Content-length', 0)), url=u)
            return e

    def iterentries(self, path):
        u = self.base + path + "/"
        resp = self.cache.request(u)
        html = lxml.html.fromstring(resp.content)
        for link in html.xpath(self.regex):
            e = entry.Entry()
            name = parse.unquote(link.encode().decode())
            isfolder = False
            url = None
            if name.endswith("/"):
                isfolder = True
                name = name[:-1]
            if not isfolder:
                url = u + link
            e.set(name=name, isfolder=isfolder, url=url, filesize=0)
            yield e
