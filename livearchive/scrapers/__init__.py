from .ia import InternetArchive
from .theeye import TheEye


classes = [InternetArchive, TheEye]


def getscrapers(cache):
    scrapers = []
    for scraper in classes:
        scrapers.append(scraper(cache))
    return scrapers
