'''
Created on Jun 9, 2024

@author: boogie
'''
from livearchive.scrapers.theeye import TheEye


class MyRient(TheEye):
    base = "https://myrient.erista.me/files/"
    name = "My Rient"
    regex = ".//tr[position()>1]/td[@class='link']/a/@href"
