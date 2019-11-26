#   Vintel - Visual Intel Chat Analyzer
#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
#

import requests
from bs4 import BeautifulSoup
from vi.cache.cache import Cache


class Regions:
    DOTLAN_REGION_URL = u"http://evemaps.dotlan.net/map"
    CACHE_TIME= 90 * 24 * 60 * 60
    def __init__(self):
        cache = Cache()
        self.regions = dict()
        svg = cache.getFromCache("regions")
        if not svg:
            url = self.DOTLAN_REGION_URL
            content = requests.get(url).text
            soup = BeautifulSoup(content, 'html.parser')
            cls = soup.find(class_='listmaps')
            cls = cls.find(class_='clearbox')
            hrefs = cls.find_all('a', href=True)
            for href in hrefs:
                self.regions[href.text] = href.attrs['href']
            if len(self.regions) > 0:
                cache.putIntoCache("regions", str(",".join("{}.{}".format(key, val) for key, val in self.regions.items())), self.CACHE_TIME)
        else:
            tregions = str(svg).split(",")
            for region in tregions:
                reg = region.split(".")
                self.regions[reg[0]] = reg[1]

    def getNames(self):
        return self.regions.keys()

    def getUrlPart(self, region: 'str'):
        if region in self.regions.keys():
            return str(self.regions[region]).replace("/map/", "")
        return None

    def __repr__(self):
        return ",".join("{}.{}".format(key, val) for key, val in self.regions.items())

def convertRegionName(name):
    """
        Converts a (system)name to the format that dotland uses
    """
    converted = []
    nextUpper = False

    for index, char in enumerate(name):
        if index == 0:
            converted.append(char.upper())
        else:
            if char in (u" ", u"_"):
                char = "_"
                nextUpper = True
            else:
                if nextUpper:
                    char = char.upper()
                else:
                    char = char.lower()
                nextUpper = False
            converted.append(char)
    return u"".join(converted)
