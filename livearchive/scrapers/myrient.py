'''
Created on Jun 9, 2024

@author: boogie
'''
from livearchive.scrapers import theeye


class MyRient(theeye.TheEye):
    base = "https://myrient.erista.me/files/"
    name = "My Rient"
    xpath_link = ".//tr[position()>1]"

    def link2addr(self, link):
        return link.xpath(".//a/@href")[0]

    def link2size(self, link):
        return link.xpath(".//td[2]")[0].text
