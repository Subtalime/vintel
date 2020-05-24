###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
# 																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
# 																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
# 																		  #
# 																		  #
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
		the tree and so the original generator is no longer stable.
"""

import six
import re
import logging
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag
from vi import states
from vi.esi.esihelper import EsiHelper

LOGGER = logging.getLogger(__name__)

CHARS_TO_IGNORE = ("*", "?", ",", "!", ".", "(", ")", "+", ":")


def bs_text_replace(navigable_string: NavigableString, new_text: str) -> None:
    new_elements = []
    for newPart in (
        BeautifulSoup("<t>{}</t>".format(new_text), "html.parser")
        .select("t")[0]
        .contents
    ):
        new_elements.append(newPart)
    try:
        for newElement in new_elements:
            navigable_string.insert_before(newElement)
        navigable_string.replace_with(six.text_type(""))
    except Exception as e:
        pass


def parse_status(navigable_string: NavigableString) -> states:
    """
    parse the Chat-Line to see if there are any System-Statuses triggered
    """
    texts = [t for t in navigable_string.contents if isinstance(t, NavigableString)]
    for text in texts:
        upperText = text.strip().upper()
        originalText = upperText
        for char in CHARS_TO_IGNORE:
            upperText = upperText.replace(char, "")
        upperWords = upperText.split()
        if ("CLEAR" in upperWords or "CLR" in upperWords) and not originalText.endswith(
            "?"
        ):
            return states.CLEAR
        elif "STAT" in upperWords or "STATUS" in upperWords:
            return states.REQUEST
        elif "?" in originalText:
            return states.REQUEST
        elif text.strip().upper() in (
            "BLUE",
            "BLUES ONLY",
            "ONLY BLUE",
            "STILL BLUE",
            "ALL BLUES",
        ):
            return states.CLEAR
    return states.ALARM


def parseShips(navigable_string: NavigableString) -> bool:
    """
    check the Chat-Entry to see if any ships are mentioned. If so, tag them with "ship_name"
    :param rtext: Tag
    :return: bool if content has changed
    """

    def format_ship_name(text: str, realShipName: str, word: str, tooltip: str) -> str:
        new_text = u"""<a style="color:green;font-weight:bold" title="{2}" href="ship_name/{0}">{1}</a>"""
        return text.replace(word, new_text.format(realShipName, word, tooltip))

    texts = [t for t in navigable_string.contents if isinstance(t, NavigableString)]
    for text in texts:
        if len(text.strip(" ")) == 0:
            continue
        parse_text_parts = text.strip(" ").split(" ")
        for parse_part in parse_text_parts:
            upper_text = parse_part.upper()
            for char in CHARS_TO_IGNORE:
                upper_text = upper_text.replace(char, "")

            # for shipName in evegate.SHIPNAMES:
            if upper_text in EsiHelper().ShipsUpper:
                hit = True
                start = text.upper().find(upper_text)
                end = start + len(upper_text)
                if (
                    start > 0
                    and text.upper()[start - 1] not in (".", ",", " ", "X", ":")
                ) or (
                    end < len(text.upper()) - 1
                    and text.upper()[end] not in (".", ",", "S", " ", ":")
                ):
                    hit = False
                if hit:
                    ship_in_text = text[start:end]
                    ship_type = EsiHelper().esi.getShipGroupTypes(
                        EsiHelper().ShipsUpper[upper_text]["group_id"]
                    )["name"]
                    LOGGER.debug('ESI found a ship "%s"', ship_in_text)
                    formatted = format_ship_name(text, ship_in_text, parse_part, ship_type)
                    bs_text_replace(text, formatted)
                    return True
    return False


def parseSystems(
    systems: list, navigable_string: NavigableString, found_systems: list
) -> bool:
    """
    check for any System-Names or Gates mentioned in the Chat-Entry
    :param systems:
    :param navigable_string:
    :param found_systems:
    :return: bool
    """
    systemNames = systems.keys()
    # words to ignore on the system parser. use UPPER CASE
    WORDS_TO_IGNORE = ("IN", "IS", "AS")

    def formatSystem(text, word, system):
        new_text = u"""<a style="color:#CC8800;font-weight:bold" href="mark_system/{0}">{1}</a>"""
        return text.replace(word, new_text.format(system, word))

    texts = [
        t for t in navigable_string.contents if isinstance(t, NavigableString) and len(t)
    ]
    for wtIdx, text in enumerate(texts):
        worktext = text
        for char in CHARS_TO_IGNORE:
            worktext = worktext.replace(char, "")
        # Drop redundant whitespace so as to not throw off word index
        worktext = " ".join(worktext.split())
        words = worktext.split(" ")

        for idx, word in enumerate(words):
            # Is this about another a system's gate?
            if len(words) > idx + 1:
                if words[idx + 1].upper() == "GATE":
                    bailout = True
                    if len(words) > idx + 2:
                        if words[idx + 2].upper() == "TO":
                            # Could be '___ GATE TO somewhere' so check this one.
                            bailout = False
                    if bailout:
                        # '_____ GATE' mentioned in message, which is not what we're
                        # interested in, so go to checking next word.
                        continue
            upperWord = word.upper()
            if upperWord != word and upperWord in WORDS_TO_IGNORE:
                continue
            if upperWord in systemNames:  # - direct hit on name
                found_systems.append(systems[upperWord])  # of the system?
                LOGGER.debug('Found a system "{}"'.format(upperWord))
                formattedText = formatSystem(text, word, upperWord)
                bs_text_replace(text, formattedText)
                return True
            elif 1 < len(upperWord) < 5:  # - upperWord < 4 chars.
                for system in systemNames:  # system begins with?
                    if system.startswith(upperWord):
                        LOGGER.debug('Using beginning part of System-Name "{}" as "{}"'.format(upperWord, system))
                        found_systems.append(systems[system])
                        formattedText = formatSystem(text, word, system)
                        bs_text_replace(text, formattedText)
                        return True
            elif "-" in upperWord and len(upperWord) > 2:  # - short with - (minus)
                upperWordParts = upperWord.split("-")  # (I-I will match I43-IF3)
                for system in systemNames:
                    systemParts = system.split("-")
                    if (
                        len(upperWordParts) == 2
                        and len(systemParts) == 2
                        and len(upperWordParts[0]) > 1
                        and len(upperWordParts[1]) > 1
                        and len(systemParts[0]) > 1
                        and len(systemParts[1]) > 1
                        and len(upperWordParts) == len(systemParts)
                        and upperWordParts[0][0] == systemParts[0][0]
                        and upperWordParts[1][0] == systemParts[1][0]
                    ):
                        LOGGER.debug('Using some part of System-Name "{}" as "{}"'.format(upperWord, system))
                        found_systems.append(systems[system])
                        formattedText = formatSystem(text, word, system)
                        bs_text_replace(text, formattedText)
                        return True
            elif len(upperWord) > 1:  # what if F-YH58 is named FY?
                for system in systemNames:
                    clearedSystem = system.replace("-", "")
                    if clearedSystem.startswith(upperWord):
                        LOGGER.debug('Using shortcut of System-Name "{}" as "{}"'.format(upperWord, system))
                        found_systems.append(systems[system])
                        formattedText = formatSystem(text, word, system)
                        bs_text_replace(text, formattedText)
                        return True
    return False


def parseUrls(navigable_string: NavigableString) -> bool:
    """
    check the Chat-Message for any URLs and tag appropiately
    :param navigable_string:
    :return:
    """

    def find_urls(s):
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

    def format_url(text, url):
        new_text = (
            u"""<a style="color:#28a5ed;font-weight:bold" href="link/{0}">{0}</a>"""
        )
        return text.replace(url, new_text.format(url))

    texts = [t for t in navigable_string.contents if isinstance(t, NavigableString)]
    for text in texts:
        urls = find_urls(text)
        for url in urls:
            bs_text_replace(text, format_url(text, url))
            return True


def parseCharnames(navigable_string: NavigableString) -> bool:
    """
    check the Chat-Entry for any Character-Names and mark them with "show_enemy"
    :param navigable_string:
    :return:
    """
    MAX_WORDS_FOR_CHARACTERNAME = 3

    def find_names(text: NavigableString) -> dict:
        WORDS_TO_IGNORE = ("IN", "IS", "AS", "AND")

        def chunks(listofwords: list, size: int = 1, offset=0) -> list:
            return [
                " ".join(listofwords[pos : pos + size])
                for pos in range(0 + offset, len(listofwords), size)
            ]

        names_list = {}
        if len(text.strip()) == 0:
            return names_list

        words = text.split()
        # chunks of 2s
        LOGGER.debug("Analysing Names in: %r", words)
        try:
            for pairs in range(MAX_WORDS_FOR_CHARACTERNAME, 0, -1):
                checklist = chunks(words, pairs)
                for check_name in checklist:
                    original_name = check_name
                    for char in CHARS_TO_IGNORE:
                        check_name = check_name.replace(char, "")
                    if check_name.upper() in WORDS_TO_IGNORE:
                        continue
                    if len(check_name) >= 3:
                        found = False
                        for a in names_list.items():
                            if re.search(check_name, a[0], re.IGNORECASE):
                                LOGGER.debug(
                                    'a part of "%s" was previously found', check_name
                                )
                                found = True
                                break
                        if not found:
                            LOGGER.debug(
                                'Couldn\'t find "%s" in list of "%r" names',
                                check_name,
                                names_list.keys(),
                            )
                            char = EsiHelper().checkPlayerName(check_name)
                            if char is not None:
                                LOGGER.debug('ESI found the character "%s"', check_name)
                                names_list[original_name] = char
            LOGGER.debug("Found names: %r", names_list.keys())
        except Exception as e:
            LOGGER.error("Error parsing Names in %s: %r", text, e)
        return names_list

    def format_charname(use_text: str, charname: str, esi_character: dict):
        format_text = u"""<a style="color:purple;font-weight:bold" href="show_enemy/{1}">{0}</a>"""
        return re.sub(" +", " ", use_text).replace(
            charname, format_text.format(charname, esi_character["id"])
        )

    texts = [
        t
        for t in navigable_string.contents
        if isinstance(t, NavigableString) and len(t) >= 3
    ]

    replaced = False
    for text in texts:  # iterate through each
        names = find_names(text)  # line
        for name, esi_char in names.items():
            new_text = format_charname(text, name, esi_char)
            bs_text_replace(text, new_text)
            replaced = True
    return replaced


if __name__ == "__main__":
    chat_text = (
        "Zedan Chent-Shi  in B-7DFU in a Merlin together "
        "with  Tablot Manzari  and  Sephora Dunn  in "
        "Dominix  AntsintheEyeJohnsen  +4  4K-TRB"
    )
    charnames = ["Zedan Chent-Shi", "Merlin", "Tablot Manzari"]

    chat_text = (
        "AsicMiner9 one  red to  8RQJ-2  julius squeezerofficer maj gendelve.imperium"
    )
    formatedText = u"<rtext>{0}</rtext>".format(chat_text)
    soup = BeautifulSoup(formatedText, "html.parser")
    navi_string = soup.select("rtext")[0]
    from vi.esi.esiinterface import EsiInterface
    from vi.resources import getVintelDir

    EsiInterface(cache_dir=getVintelDir())

    while parseCharnames(navi_string):
        continue
    LOGGER.debug("Names found: %r", navi_string)
    exit(0)
    text_parts = chat_text.strip(" ").split(" ")
    checkwords = ""
    while len(text_parts) > 0:
        for part in text_parts:
            checkwords += " " + part
            checkwords = checkwords.lstrip(" ")
            originalText = checkwords
            if len(checkwords) > 3:
                if checkwords in charnames:
                    print("Hit with {}".format(checkwords))
                    # last hit
                    index = text_parts.index(part)
                    i = 0
                    while i < index:
                        text_parts.pop(0)
                        i += 1
                    break
        checkwords = ""
        text_parts.pop(0)
