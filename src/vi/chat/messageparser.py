#     Vintel - Visual Intel Chat Analyzer
#     Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#
import datetime
import logging
import re

import six
from bs4 import BeautifulSoup, NavigableString

from vi.chat.chatmessage import Message
from vi.esi.esihelper import EsiHelper
from vi.settings.settings import GeneralSettings
from vi.states import State


class MessageParserException(Exception):
    pass


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


def parse_line(line: str) -> tuple:
    # finding the timestamp
    time_start = line.find("[") + 1
    time_ends = line.find("]")
    time_str = line[time_start:time_ends].strip()
    try:
        utc_timestamp = datetime.datetime.strptime(time_str, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        raise MessageParserException("Invalid Timestamp in Line: %s" % (line,))
    # all Log-Lines are logged in UTC format, so make it Local time
    # timestamp = utc_timestamp.replace(tzinfo=None)
    timestamp = (
        utc_timestamp.replace(tzinfo=datetime.timezone.utc)
        .astimezone(tz=None)
        .replace(tzinfo=None)
    )
    # finding the username of the poster
    user_ends = line.find(">")
    username = line[time_ends + 1 : user_ends].strip()
    # finding the pure message
    text = line[user_ends + 1 :].strip()  # text will the text to work an
    return utc_timestamp, username, text, timestamp


class MessageParser:
    CHARS_TO_IGNORE = ("*", "?", ",", "!", ".", "(", ")", "+", ":")
    WORDS_TO_IGNORE = ("IN", "IS", "AS", "AND")

    def __init__(
        self,
        room_name: str,
        char_name: str,
        locations: dict,
        is_local: bool,
        max_age: int = 300,
    ):
        self.LOGGER = logging.getLogger(__name__)
        self.room_name = room_name
        self.char_name = char_name
        self.locations = locations
        self.message_age = max_age
        self.local_room = is_local
        ctoi = ["\\{0}".format(i) for i in self.CHARS_TO_IGNORE]
        self.chars_to_ignore = re.compile(r'(' + '|'.join(ctoi) + r')', flags=re.IGNORECASE)
        self.words_to_ignore = re.compile(r'\b(' + "|".join(self.WORDS_TO_IGNORE) + r')\b', flags=re.IGNORECASE)
        self.names_list = []
        if len(self.locations) == 0:
            self.locations = {
                "system": "?",
                "timestamp": datetime.datetime.now() - datetime.timedelta(days=1),
            }

    def process_systems(self, dotlan_systems: dict, message: Message) -> bool:
        if self.local_room or not message.navigable_string:
            return False
        count = 0
        while self._parse_systems(dotlan_systems, message):
            count += 1
            if count > 5:
                self.LOGGER.warning(
                    "parseSystems excessive runs on %r" % (message.rtext,)
                )
                break
        return count > 0

    def process_ships(self, message: Message) -> bool:
        if not message.navigable_string:
            return False
        count = 0
        while self._parse_ships(message):
            count += 1
            if count > 5:
                self.LOGGER.warning(
                    "process_ships excessive runs on %r" % (message.rtext,)
                )
                break
        return count > 0

    def process_urls(self, message: Message) -> bool:
        if not message.navigable_string:
            return False
        count = 0
        while self._parse_urls(message):
            count += 1
            if count > 5:
                self.LOGGER.warning("parseUrls excessive runs on %r" % (message.rtext,))
                break
        return count > 0

    def process_charnames(self, message: Message) -> bool:
        if not message.navigable_string:
            return False
        count = 0
        while self._parse_charnames(message):
            count += 1
            if count > 5:
                self.LOGGER.warning(
                    "process_charnames excessive runs on %r" % (message.rtext,)
                )
                break
        return count > 0

    def process(self, line) -> object:
        """process a Log-Line.
        """
        message = None
        utctime, username, text, timestamp = parse_line(line)
        # anything older than max_age, ignore
        if (datetime.datetime.utcnow() - utctime).total_seconds() > self.message_age:
            self.LOGGER.debug(
                "%s/%s: Message-Line too old: %s"
                % (self.room_name, self.char_name, line,)
            )
            return message
        if username in ("EVE-System", "EVE System"):
            # System-Message indicates location of current character
            if ":" in text:
                system = text.split(":")[1].strip().replace("*", "").upper()
                status = State["LOCATION"]
            else:
                # We could not determine if the message was system-change related
                system = "?"
                status = State["IGNORE"]
            if timestamp > self.locations["timestamp"]:
                self.locations["system"] = system
                self.locations["timestamp"] = timestamp
                message = Message(
                    self.room_name,
                    text,
                    timestamp,
                    self.char_name,
                    currsystems=[system],
                    status=status,
                    log_line=line,
                    utc=utctime,
                )
            return message
        original_text = text
        formatted_text = u"<rtext>{0}</rtext>".format(text)
        soup = BeautifulSoup(formatted_text, "html.parser")
        navi_text = soup.select("rtext")[0]
        upper_text = text.upper()
        if self.room_name.startswith("="):
            return Message(
                self.room_name,
                "xxx " + text,
                timestamp,
                username,
                status=State["KOS_STATUS_REQUEST"],
                rtext=navi_text,
                plain_text=original_text,
                upper_text=upper_text,
                log_line=line,
                utc=utctime,
            )
        # KOS request
        elif upper_text.startswith("XXX "):
            return Message(
                self.room_name,
                text,
                timestamp,
                username,
                rtext=navi_text,
                status=State["KOS_STATUS_REQUEST"],
                plain_text=original_text,
                upper_text=upper_text,
                log_line=line,
                utc=utctime,
            )
        elif upper_text.startswith("VINTELSOUND_TEST"):
            return Message(
                self.room_name,
                text,
                timestamp,
                username,
                status=State["SOUND_TEST"],
                rtext=navi_text,
                plain_text=original_text,
                upper_text=upper_text,
                log_line=line,
                utc=utctime,
            )

        parsed_status = self.get_status(navi_text)
        status = parsed_status if parsed_status is not None else State["ALARM"]
        message = Message(
            self.room_name,
            text,
            timestamp,
            username,
            status=status,
            rtext=navi_text,
            plain_text=original_text,
            upper_text=upper_text,
            log_line=line,
            utc=utctime,
        )

        return message

    def _parse_systems(self, dotlan_systems: dict, message: Message) -> bool:
        """check for any System-Names or Gates mentioned in the Chat-Entry.

        :param dotlan_systems: Map-System-Dictionary
        :type dotlan_systems: dict
        :param message: the Message to be parsed
        :type message: Message
        :return: bool: systems found in Message
        """
        system_names = set(dotlan_systems.keys())
        # words to ignore on the system parser. use UPPER CASE
        WORDS_TO_IGNORE = ("IN", "IS", "AS")

        def format_system(f_text, f_word, f_system):
            new_text = u"""<a style="color:{2};font-weight:bold" href="mark_system/{0}">{1}</a>"""
            return f_text.replace(
                f_word,
                new_text.format(f_system, f_word, GeneralSettings().color_system),
            )

        texts = [
            t
            for t in message.navigable_string.contents
            if isinstance(t, NavigableString)
            and t is not None
            and message.navigable_string.contents
        ]
        for wtIdx, text in enumerate(texts):
            work_text = text
            work_text = self.chars_to_ignore.sub("", work_text)
            # for char in self.CHARS_TO_IGNORE:
            #     work_text = work_text.replace(char, "")
            # Drop redundant whitespace so as to not throw off word index
            work_text = " ".join(work_text.split())
            words = work_text.split(" ")

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
                upper_word = word.upper()
                if upper_word != word and upper_word in WORDS_TO_IGNORE:
                    continue
                if upper_word in system_names:  # - direct hit on name
                    message.systems.append(dotlan_systems[upper_word])  # of the system?
                    self.LOGGER.debug('Found a system "{}"'.format(upper_word))
                    formatted_text = format_system(text, word, upper_word)
                    bs_text_replace(text, formatted_text)
                    return True
                elif 1 < len(upper_word) < 5:  # - upper_word < 4 chars.
                    for system in system_names:  # system begins with?
                        if system.startswith(upper_word):
                            self.LOGGER.debug(
                                'Using beginning part of System-Name "{}" as "{}"'.format(
                                    upper_word, system
                                )
                            )
                            message.systems.append(dotlan_systems[system])
                            formatted_text = format_system(text, word, system)
                            bs_text_replace(text, formatted_text)
                            return True
                elif (
                    "-" in upper_word and len(upper_word) > 2
                ):  # - short with - (minus)
                    upper_word_parts = upper_word.split("-")  # (I-I will match I43-IF3)
                    for system in system_names:
                        systemParts = system.split("-")
                        if (
                            len(upper_word_parts) == 2
                            and len(systemParts) == 2
                            and len(upper_word_parts[0]) > 1
                            and len(upper_word_parts[1]) > 1
                            and len(systemParts[0]) > 1
                            and len(systemParts[1]) > 1
                            and len(upper_word_parts) == len(systemParts)
                            and upper_word_parts[0][0] == systemParts[0][0]
                            and upper_word_parts[1][0] == systemParts[1][0]
                        ):
                            self.LOGGER.debug(
                                'Using some part of System-Name "{}" as "{}"'.format(
                                    upper_word, system
                                )
                            )
                            message.systems.append(dotlan_systems[system])
                            formatted_text = format_system(text, word, system)
                            bs_text_replace(text, formatted_text)
                            return True
                elif len(upper_word) > 1:  # what if F-YH58 is named FY?
                    for system in system_names:
                        cleared_system = system.replace("-", "")
                        if cleared_system.startswith(upper_word):
                            self.LOGGER.debug(
                                'Using shortcut of System-Name "{}" as "{}"'.format(
                                    upper_word, system
                                )
                            )
                            message.systems.append(dotlan_systems[system])
                            formatted_text = format_system(text, word, system)
                            bs_text_replace(text, formatted_text)
                            return True
        return False

    def _parse_ships(self, message: Message) -> bool:
        """
        check the Chat-Entry to see if any ships are mentioned. If so, tag them with "ship_name"
        :param rtext: Tag
        :return: bool if content has changed
        """

        def format_ship_name(
            f_text: str, f_realShipName: str, f_word: str, f_tooltip: str
        ) -> str:
            new_text = u"""<a style="color:{3};font-weight:bold" title="{2}" href="ship_name/{0}">{1}</a>"""
            return f_text.replace(
                f_word,
                new_text.format(
                    f_realShipName, f_word, f_tooltip, GeneralSettings().color_ship
                ),
            )

        # navigable_string = message.navigable_string

        texts = [
            t
            for t in message.navigable_string.contents
            if isinstance(t, NavigableString)
            and t is not None
            and message.navigable_string.contents
        ]
        for text in texts:
            if len(text.strip(" ")) == 0:
                continue
            parse_text_parts = text.strip(" ").split(" ")
            for parse_part in parse_text_parts:
                upper_text = parse_part.upper()
                # escape all cahracters
                upper_text = self.chars_to_ignore.sub("", upper_text)
                # for char in self.CHARS_TO_IGNORE:
                #     upper_text = upper_text.replace(char, "")

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
                        try:
                            ship_type = EsiHelper().esi.getShipGroupTypes(
                                EsiHelper().ShipsUpper[upper_text]["group_id"]
                            )["name"]
                            self.LOGGER.debug('ESI found a ship "%s"', ship_in_text)
                            formatted = format_ship_name(
                                text, ship_in_text, parse_part, ship_type
                            )
                            bs_text_replace(text, formatted)
                            return True
                        except TypeError as e:
                            self.LOGGER.warning(
                                "Expected to find %s as %s, but failed...",
                                ship_in_text,
                                upper_text,
                            )
                            pass
        return False

    def _parse_urls(self, message: Message) -> bool:
        """
        check the Chat-Message for any URLs and tag appropiately
        :param navigable_string:
        :return:
        """

        def find_urls(s):
            # yes, this is faster than regex and less complex to read
            f_urls = []
            prefixes = ("http://", "https://")
            for prefix in prefixes:
                start = 0
                while start >= 0:
                    start = s.find(prefix, start)
                    if start >= 0:
                        stop = s.find(" ", start)
                        if stop < 0:
                            stop = len(s)
                        f_urls.append(s[start:stop])
                        start += 1
            return f_urls

        def format_url(f_text, f_url):
            new_text = (
                u"""<a style="color:{1};font-weight:bold" href="link/{0}">{0}</a>"""
            )
            return f_text.replace(
                f_url, new_text.format(f_url, GeneralSettings().color_url)
            )

        # navigable_string = message.navigable_string
        texts = [
            t
            for t in message.navigable_string.contents
            if isinstance(t, NavigableString)
            and t is not None
            and message.navigable_string.contents
        ]
        for text in texts:
            urls = find_urls(text)
            for url in urls:
                bs_text_replace(text, format_url(text, url))
                return True

    def _parse_charnames(self, message: Message) -> bool:
        """
        check the Chat-Entry for any Character-Names and mark them with "show_enemy"
        :param navigable_string:
        :return:
        """
        MAX_WORDS_FOR_CHARACTERNAME = 3

        # simple list of words
        def build_matrix(text_line: str, separator=" ") -> list:
            text_line = self.chars_to_ignore.sub("", text_line)
            text_line = self.words_to_ignore.sub("", text_line)
            return text_line.strip().split(separator)

        # get adjacent words from list
        def coord_word(coord: tuple, matrix: list) -> str:
            return matrix[coord[0] : coord[1] + 1]

        # combine adjacent words
        def convert_to_name(coord_matrix, matrix: list, separator: str = " ") -> str:
            return separator.join(coord_word(coord_matrix, matrix))

        # build a list of coordinates based on matrix
        def build_list(
            matrix: list, maxlength: int = MAX_WORDS_FOR_CHARACTERNAME
        ) -> list:
            coord_list = []
            for l in range(maxlength, 0, -1):
                for i, word in enumerate(matrix):
                    if i + l > len(matrix):
                        break
                    coord_list.append(
                        (i, i + l - 1, convert_to_name((i, i + l - 1), matrix))
                    )
            return coord_list

        # remove a tuple match from match_list
        def does_contain(coord: tuple, match: tuple) -> bool:
            start, end, word = match
            for index in range(coord[0], coord[1] + 1):
                if start <= index <= end:
                    return True
            return False

        def find_names(matrix: list, found_names: list) -> tuple:
            for start, end, name in matrix:
                if len(name) > 3:
                    self.LOGGER.debug("Asking ESI for character '%s'", name.strip())
                    player = EsiHelper().checkPlayerName(name.strip())
                    if player:
                        self.LOGGER.debug('ESI found the character "%s"', name.strip())
                        found_names.append((name.strip(), player))
                        return start, end, name
            return 0, 0, None

        def format_charname(use_text: str, charname: str, esi_character: dict):
            format_text = u"""<a style="color:{2};font-weight:bold" href="show_enemy/{1}">{0}</a>"""
            return re.sub(r" +", r" ", use_text).replace(
                charname,
                format_text.format(
                    charname, esi_character["id"], GeneralSettings().color_character
                ),
            )

        texts = [
            t
            for t in message.navigable_string.contents
            if isinstance(t, NavigableString)
            and t is not None
            and message.navigable_string.contents
        ]
        found_names = []
        for text in texts:  # iterate through each
            matrix = build_list(build_matrix(text))
            while True:
                s, e, n = find_names(matrix, found_names)
                if not n:
                    break
                self.LOGGER.debug("Before rescan (Skip %d,%d): %r", s, e, matrix)
                matrix = [x for x in matrix if not does_contain((s, e), x)]
                self.LOGGER.debug("After rescan: %r", matrix)
            for name, esi_char in found_names:
                new_text = format_charname(text, name, esi_char)
                bs_text_replace(text, new_text)
        return len(found_names) > 0

    def get_status(self, navigable_string: NavigableString) -> State:
        """
        parse the Chat-Line to see if there are any System-Statuses triggered
        """
        texts = [
            t
            for t in navigable_string
            if isinstance(t, NavigableString) and navigable_string is not None
        ]
        for text in texts:
            upper_text = text.strip().upper()
            original_text = upper_text
            upper_text = self.chars_to_ignore.sub("", upper_text)
            # for char in self.CHARS_TO_IGNORE:
            #     upper_text = upper_text.replace(char, "")
            upper_words = upper_text.split()
            if (
                "CLEAR" in upper_words or "CLR" in upper_words
            ) and not original_text.endswith("?"):
                return State["CLEAR"]
            elif (
                "STAT" in upper_words
                or "STATUS" in upper_words
                or (
                    ("CLEAR" in upper_words or "CLR" in upper_words)
                    and original_text.endswith("?")
                )
            ):
                return State["REQUEST"]
            elif "?" in original_text:
                return State["REQUEST"]
            elif text.strip().upper() in (
                "BLUE",
                "BLUES ONLY",
                "ONLY BLUE",
                "STILL BLUE",
                "ALL BLUES",
            ):
                return State["CLEAR"]
        return State["ALARM"]


if __name__ == "__main__":
    mp = MessageParser("Test", "myself", {}, False)
    message = Message(
        "test", "this is what we aren't looking for", datetime.datetime.now(), "myself"
    )
