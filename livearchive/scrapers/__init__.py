from .ia import InternetArchive
from .theeye import TheEye
from .myrient import MyRient


classes = [InternetArchive, TheEye, MyRient]


def getscrapers(cache):
    scrapers = []
    for scraper in classes:
        scrapers.append(scraper(cache))
    return scrapers
