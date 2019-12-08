###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
#																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
#																		  #
#																		  #
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

""" 12.02.2015
	I know this is a little bit dirty, but I prefer to have all the functions
	to parse the chat in this file together.
	Wer are now work directly with the html-formatted text, which we use to
	display it. We are using a HTML/XML-Parser to have the benefit, that we
	can only work and analyze those text, that is still not on tags, because
	all the text in tags was allready identified.
	f.e. the ship_parser:
		we call it from the chat and give them the rtext (richtext).
		if the parser hits a shipname, it will modifiy the tree by creating
		a new tag and replace the old text with it (calls tet_replace),
		than it returns True.
		The chat will call the function again until it return False
		(None is False) otherwise.
		We have to call the parser again after a hit, because a hit will change
		the tree and so the original generator is not longer stable.
"""

import six
import re
import logging
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from vi import states
from vi.esi.esihelper import EsiHelper
LOGGER = logging.getLogger(__name__)

CHARS_TO_IGNORE = ("*", "?", ",", "!", ".", "(", ")", "+")


def textReplace(element: NavigableString, newText: str):
    newText = "<t>" + newText + "</t>"
    newElements = []
    for newPart in BeautifulSoup(newText, 'html.parser').select("t")[0].contents:
        newElements.append(newPart)
    try:
        for newElement in newElements:
            element.insert_before(newElement)
        element.replace_with(six.text_type(""))
    except Exception:
        pass


def parseStatus(rtext):
    """
    parse the Chat-Line to see if there are any System-Statuses triggered
    """
    texts = [t for t in rtext.contents if isinstance(t, NavigableString)]
    for text in texts:
        upperText = text.strip().upper()
        originalText = upperText
        for char in CHARS_TO_IGNORE:
            upperText = upperText.replace(char, "")
        upperWords = upperText.split()
        if (("CLEAR" in upperWords or "CLR" in upperWords) and not originalText.endswith("?")):
            return states.CLEAR
        elif ("STAT" in upperWords or "STATUS" in upperWords):
            return states.REQUEST
        elif ("?" in originalText):
            return states.REQUEST
        elif (text.strip().upper() in ("BLUE", "BLUES ONLY", "ONLY BLUE",
                                       "STILL BLUE", "ALL BLUES")):
            return states.CLEAR


def parseShips(rtext: Tag) -> bool:
    """
    check the Chat-Entry to see if any ships are mentioned. If so, tag them with "ship_name"
    :param rtext: Tag
    :return: bool if content has changed
    """
    def formatShipName(text: str, realShipName: str, word: str, tooltip: str) -> str:
        newText = u"""<a style="color:green;font-weight:bold" title="{2}" href="ship_name/{0}">{1}</a>"""
        text = text.replace(word, newText.format(realShipName, word, tooltip))
        return text

    texts = [t for t in rtext.contents if isinstance(t, NavigableString)]
    for text in texts:
        if len(text.strip(" ")) == 0:
            continue
        parts = text.strip(" ").split(" ")
        for part in parts:
            upperText = part.upper()
            for char in CHARS_TO_IGNORE:
                upperText = upperText.replace(char, "")

            # for shipName in evegate.SHIPNAMES:
            if upperText in EsiHelper().ShipsUpper:
                hit = True
                start = text.upper().find(upperText)
                end = start + len(upperText)
                if ((start > 0 and text.upper()[start - 1] not in (".", ",", " ", "X"))
                        or (end < len(text.upper()) - 1 and
                            text.upper()[end] not in (".", ",", "S", " "))):
                    hit = False
                if hit:
                    shipInText = text[start:end]
                    shipType=EsiHelper().esi.getShipGroupTypes(EsiHelper().ShipsUpper[upperText]['group_id'])['name']
                    formatted = formatShipName(text, shipInText, part, shipType)
                    textReplace(text, formatted)
                    return True


def parseSystems(systems: list, rtext: Tag, foundSystems: list) -> bool:
    """
    check for any System-Names or Gates mentioned in the Chat-Entry
    :param systems:
    :param rtext:
    :param foundSystems:
    :return: bool
    """
    systemNames = systems.keys()
    # words to ignore on the system parser. use UPPER CASE
    WORDS_TO_IGNORE = ("IN", "IS", "AS")

    def formatSystem(text, word, system):
        newText = u"""<a style="color:#CC8800;font-weight:bold" href="mark_system/{0}">{1}</a>"""
        text = text.replace(word, newText.format(system, word))
        return text

    texts = [t for t in rtext.contents if isinstance(t, NavigableString) and len(t)]    
    for wtIdx, text in enumerate(texts):
        worktext = text
        for char in CHARS_TO_IGNORE:
            worktext = worktext.replace(char, "")
        # Drop redundant whitespace so as to not throw off word index
        worktext = ' '.join(worktext.split())
        words = worktext.split(" ")

        for idx, word in enumerate(words):
            # Is this about another a system's gate?
            if len(words) > idx + 1:
                if words[idx+1].upper() == 'GATE':
                    bailout = True
                    if len(words) > idx + 2:
                        if words[idx+2].upper() == 'TO':
                            # Could be '___ GATE TO somewhere' so check this one.
                            bailout = False
                    if bailout:
                        # '_____ GATE' mentioned in message, which is not what we're
                        # interested in, so go to checking next word.
                        continue
            upperWord = word.upper()
            if upperWord != word and upperWord in WORDS_TO_IGNORE: continue
            if upperWord in systemNames:  # - direct hit on name
                foundSystems.append(systems[upperWord])  # of the system?
                formattedText = formatSystem(text, word, upperWord)
                textReplace(text, formattedText)
                return True
            elif 1 < len(upperWord) < 5:  # - upperWord < 4 chars.
                for system in systemNames:  # system begins with?
                    if system.startswith(upperWord):
                        foundSystems.append(systems[system])
                        formattedText = formatSystem(text, word, system)
                        textReplace(text, formattedText)
                        return True
            elif "-" in upperWord and len(upperWord) > 2:  # - short with - (minus)
                upperWordParts = upperWord.split("-")  # (I-I will match I43-IF3)
                for system in systemNames:
                    systemParts = system.split("-")
                    if (len(upperWordParts) == 2 and len(systemParts) == 2
                            and len(upperWordParts[0]) > 1 and len(upperWordParts[1]) > 1
                            and len(systemParts[0]) > 1 and len(systemParts[1]) > 1
                            and len(upperWordParts) == len(systemParts)
                            and upperWordParts[0][0] == systemParts[0][0]
                            and upperWordParts[1][0] == systemParts[1][0]):
                        foundSystems.append(systems[system])
                        formattedText = formatSystem(text, word, system)
                        textReplace(text, formattedText)
                        return True
            elif len(upperWord) > 1:  # what if F-YH58 is named FY?
                for system in systemNames:
                    clearedSystem = system.replace("-", "")
                    if clearedSystem.startswith(upperWord):
                        foundSystems.append(systems[system])
                        formattedText = formatSystem(text, word, system)
                        textReplace(text, formattedText)
                        return True
    return False


def parseUrls(rtext: Tag) -> bool:
    """
    check the Chat-Message for any URLs and tag appropiately
    :param rtext:
    :return:
    """
    def findUrls(s):
        # yes, this is faster than regex and less complex to read
        urls = []
        prefixes = ("http://", "https://")
        for prefix in prefixes:
            start = 0
            while start >= 0:
                start = s.find(prefix, start)
                if start >= 0:
                    stop = s.find(" ", start)
                    if stop < 0:
                        stop = len(s)
                    urls.append(s[start:stop])
                    start += 1
        return urls

    def formatUrl(text, url):
        newText = u"""<a style="color:#28a5ed;font-weight:bold" href="link/{0}">{0}</a>"""
        text = text.replace(url, newText.format(url))
        return text

    texts = [t for t in rtext.contents if isinstance(t, NavigableString)]
    for text in texts:
        urls = findUrls(text)
        for url in urls:
            textReplace(text, formatUrl(text, url))
            return True


def parseCharnames(rtext: Tag) -> bool:
    """
    check the Chat-Entry for any Character-Names and mark them with "show_enemy"
    :param rtext:
    :return:
    """
    MAX_WORDS_FOR_CHARACTERNAME = 3
    def findNames(text: NavigableString) -> dict:
        WORDS_TO_IGNORE = ("IN", "IS", "AS", "AND")
        def chunks(listofwords: list, size: int=1, offset=0) -> list:
            return [" ".join(listofwords[pos:pos + size]) for pos in range(0 + offset,
                                                                           len(listofwords),
                                                                           size)]

        names = {}
        if len(text.strip()) == 0:
            return names

        words = text.split()
        # chunks of 2s
        LOGGER.debug("Analysing Names in: {}".format(words))
        try:
            for pairs in range(MAX_WORDS_FOR_CHARACTERNAME,0,-1):
                checklist = chunks(words, pairs)
                for checkname in checklist:
                    origname = checkname
                    for char in CHARS_TO_IGNORE:
                        checkname = checkname.replace(char, "")
                    if checkname.upper() in WORDS_TO_IGNORE:
                        continue
                    if len(checkname) >= 3:
                        found = False
                        for a in names.items():
                            if re.search(checkname, a[0], re.IGNORECASE):
                                LOGGER.debug("a part of \"{}\" was previously found".format(checkname))
                                found = True
                                break
                        if not found:
                            LOGGER.debug("Couldn't find \"%s\" in list of \"%r\" names" % (checkname, names))
                            char = EsiHelper().checkPlayerName(checkname)
                            if char is not None:
                                LOGGER.debug("ESI found the character \"{}\"".format(checkname))
                                names[origname] = char
            LOGGER.debug("Found names: {}".format(names))
        except Exception as e:
            LOGGER.error("Error parsing Names", e)
        return names

    def formatCharname(text: str, charname: str, esicharacter: dict):
        formatText = u"""<a style="color:purple;font-weight:bold" href="show_enemy/{1}">{0}</a>"""
        newtext = text.replace(charname, formatText.format(charname, esicharacter["id"]))
        return newtext

    texts = [t for t in rtext.contents if isinstance(t, NavigableString) and len(t) >= 3]

    replaced = False
    for text in texts:  # iterate through each
        names = findNames(text)  # line
        for name, chara in names.items():
            newText = formatCharname(text, name, chara)
            textReplace(text, newText)
            replaced = True
    return replaced


if __name__ == "__main__":
    chat_text = "Zedan Chent-Shi  in B-7DFU in a Merlin together " \
                "with  Tablot Manzari  and  Sephora Dunn  in " \
                "Dominix  AntsintheEyeJohnsen  +4  4K-TRB"
    charnames = ["Zedan Chent-Shi", "Merlin", "Tablot Manzari"]

    formatedText = u"<rtext>{0}</rtext>".format(chat_text)
    soup = BeautifulSoup(formatedText, 'html.parser')
    rtext = soup.select("rtext")[0]
    from vi.esi.esiinterface import EsiInterface
    from vi.resources import getVintelDir
    EsiInterface(cache_dir=getVintelDir())

    while parseCharnames(rtext):
        continue
    LOGGER.debug("Names found: %r", rtext)
    exit(0)
    parts = chat_text.strip(" ").split(" ")
    checkwords = ""
    while len(parts) > 0:
        for part in parts:
            checkwords += " " + part
            checkwords = checkwords.lstrip(" ")
            originalText = checkwords
            if len(checkwords) > 3:
                if checkwords in charnames:
                    print("Hit with {}".format(checkwords))
                    # last hit
                    index = parts.index(part)
                    i = 0
                    while i < index:
                        parts.pop(0)
                        i += 1
                    break
        checkwords = ""
        parts.pop(0)
