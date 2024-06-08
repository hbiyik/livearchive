from .ia import InternetArchive
from .theeye import TheEye


def getscrapers(cache):
    scrapers = []
    for scraper in [InternetArchive, TheEye]:
        scrapers.append(scraper(cache))
    return scrapers
