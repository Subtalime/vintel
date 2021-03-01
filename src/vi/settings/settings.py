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
import logging
import os
import pickle

from vi.cache import Cache
from vi.resources import get_sound_resource_path
from vi.states import State


class _Settings:
    """base class to store settings in cache, but provide an easy interface without
    having to remember the "cache_name" variable

    """
    def __init__(self, cache_storage):
        """you can provide your own Storage-Function (i.e. for testing)

        :param cache_storage: class, which provides same "fetch/put" facilities as "Cache"
        """
        self._cache = cache_storage
        if not cache_storage:
            self._cache = Cache()
        self._config = {}
        self.KEY = "OVERRIDE"
        res = self._cache.fetch("my_settings", outdated=True)
        if res:
            self._config = res
        self.defaults = {}

    def _set_property(self):
        self._cache.put("my_settings", self._config)

    def _get_property(self, property_name):
        try:
            return self._config[property_name]
        except KeyError:
            return None

    @property
    def setting(self):
        # this will return the dictionary of self.KEY
        value = self._get_property(self.KEY)
        # do we need to set the defaults (nothing in cache, or false SAVE)
        if value is None or not isinstance(value, dict):
            value = self.defaults
        for default in self.defaults:
            if default not in value.keys():
                value[default] = self.defaults[default]
        return value

    @setting.setter
    def setting(self, value):
        if self.KEY not in self._config.keys():
            self._config[self.KEY] = self.defaults
        k = list(value.keys())[0]
        if k not in set(self._config[self.KEY].keys()):
            logging.getLogger(__name__).error(
                f"Key '{k}' not in {self.KEY} Configuration"
            )
        self._config[self.KEY][k] = value[k]
        self._set_property()


class RegionSettings(_Settings):
    """anything to do with Regions and Maps
    """
    def __init__(self, cache_storage=None):
        super().__init__(cache_storage)
        self.KEY = "regions"
        self.defaults = {
            "region_names": "delve,querious",
            "selected": "delve",
            "jump_bridge_url": None,
            "jump_bridge_data": None,
        }

    @property
    def selected_region(self) -> str:
        return str(self.setting["selected"])

    @selected_region.setter
    def selected_region(self, value: str):
        v = {"selected": str(value)}
        self.setting = v

    @property
    def region_names(self) -> str:
        return str(self.setting["region_names"])

    @region_names.setter
    def region_names(self, value: str):
        v = {"region_names": str(value)}
        self.setting = v

    @property
    def jump_bridge_url(self) -> str:
        return str(self.setting["jump_bridge_url"])

    @jump_bridge_url.setter
    def jump_bridge_url(self, value: str):
        v = {"jump_bridge_url": str(value)}
        self.setting = v

    @property
    def jump_bridge_data(self) -> list:
        return self.setting["jump_bridge_data"]

    @jump_bridge_data.setter
    def jump_bridge_data(self, value: list):
        v = {"jump_bridge_data": value}
        self.setting = v


class ColorSettings(_Settings):
    """color values for Map indicators and alarms
    """
    def __init__(self, cache_storage=None):
        super().__init__(cache_storage)
        self.KEY = "colors"
        self.defaults = {
            "js_alarm_colors": {
                State["ALARM"]: [
                    [60 * 5, "#FF0000", "#FFFFFF"],
                    [60 * 10, "#FF9B0F", "#000000"],
                    [60 * 15, "#FFFA0F", "#000000"],
                ],
                State["REQUEST"]: [[60 * 2, "#ffaaff", "#000000"],],
                State["CLEAR"]: [[60 * 2, "#59FF6C", "#000000"],],
            }
        }

    @property
    def js_alarm_colors(self) -> dict:
        return dict(self.setting["js_alarm_colors"])

    @js_alarm_colors.setter
    def js_alarm_colors(self, value: dict):
        v = {"js_alarm_colors": dict(value)}
        self.setting = v


class ChatroomSettings(_Settings):
    """chat-room monitoring
    """
    def __init__(self, cache_storage=None):
        super().__init__(cache_storage)
        self.KEY = "chatroom"
        self.defaults = {"room_names": "querius.imperium,delve.imperium"}

    @property
    def room_names(self) -> str:
        return str(self.setting["room_names"])

    @room_names.setter
    def room_names(self, value: str):
        v = {"room_names": str(value)}
        self.setting = v


class SoundSettings(_Settings):
    """what sound to play on what alarm
    """
    def __init__(self, cache_storage=None):
        super().__init__(cache_storage)
        self.KEY = "sound"
        self._defaults()

    def _defaults(self):
        listing = []
        for distance in range(0, 6):
            entry = [
                "{} Jumps".format(distance),
                os.path.join(get_sound_resource_path(), "alert.wav"),
                25,
            ]
            listing.append(entry)
        listing.append(["KOS", os.path.join(get_sound_resource_path(), "warning.wav"), 25])
        listing.append(["Request", os.path.join(get_sound_resource_path(), "request.wav"), 25])
        self.defaults = {
            "sound": listing,
        }

    @property
    def sound(self) -> list:
        return self.setting["sound"]

    @sound.setter
    def sound(self, value):
        v = {"sound": list(value)}
        self.setting = v


class GeneralSettings(_Settings):
    """all individual values you want stored
    """
    def __init__(self, cache_storage=None):
        super().__init__(cache_storage)
        self.KEY = "general"
        self.defaults = {
            "message_expiry": 20 * 60,
            "clipboard_check_interval": 4 * 1000,
            "ship_parser": False,
            "character_parser": True,
            "self_notify": True,
            "popup_notification": True,
            "alarm_distance": 2,
            "background_color": "#ffffff",
            "map_update_interval": 4 * 1000,
            "sound_active": True,
            "show_requests": True,
            "log_level": 10,
            "color_system": "#CC8800",
            "color_character": "purple",
            "color_ship": "green",
            "color_url": "#28a5ed",
        }

    @property
    def color_system(self) -> str:
        return str(self.setting["color_system"])

    @color_system.setter
    def color_system(self, value: str):
        v = {"color_system": str(value)}
        self.setting = v

    @property
    def color_ship(self) -> str:
        return str(self.setting["color_ship"])

    @color_ship.setter
    def color_ship(self, value: str):
        v = {"color_ship": str(value)}
        self.setting = v

    @property
    def color_url(self) -> str:
        return str(self.setting["color_url"])

    @color_url.setter
    def color_url(self, value: str):
        v = {"color_url": str(value)}
        self.setting = v

    @property
    def color_character(self) -> str:
        return str(self.setting["color_character"])

    @color_character.setter
    def color_character(self, value: str):
        v = {"color_character": str(value)}
        self.setting = v

    @property
    def sound_active(self) -> bool:
        return bool(self.setting["sound_active"])

    @sound_active.setter
    def sound_active(self, value: bool):
        v = {"sound_active": bool(value)}
        self.setting = v

    @property
    def log_level(self) -> int:
        return int(self.setting["log_level"])

    @log_level.setter
    def log_level(self, value: int):
        v = {"log_level": int(value)}
        self.setting = v

    @property
    def show_requests(self) -> bool:
        return bool(self.setting["show_requests"])

    @show_requests.setter
    def show_requests(self, value: bool):
        v = {"show_requests": bool(value)}
        self.setting = v

    @property
    def character_parser(self) -> bool:
        return bool(self.setting["character_parser"])

    @character_parser.setter
    def character_parser(self, value: bool):
        v = {"character_parser": bool(value)}
        self.setting = v

    @property
    def ship_parser(self) -> bool:
        return bool(self.setting["ship_parser"])

    @ship_parser.setter
    def ship_parser(self, value: bool):
        v = {"ship_parser": bool(value)}
        self.setting = v

    @property
    def popup_notification(self) -> bool:
        return bool(self.setting["popup_notification"])

    @popup_notification.setter
    def popup_notification(self, value: bool):
        v = {"popup_notification": bool(value)}
        self.setting = v

    @property
    def self_notify(self) -> bool:
        return bool(self.setting["self_notify"])

    @self_notify.setter
    def self_notify(self, value: bool):
        v = {"self_notify": bool(value)}
        self.setting = v

    @property
    def background_color(self) -> str:
        return str(self.setting["background_color"])

    @background_color.setter
    def background_color(self, value: str):
        v = {"background_color": str(value)}
        self.setting = v

    @property
    def message_expiry(self) -> int:
        return int(self.setting["message_expiry"])

    @message_expiry.setter
    def message_expiry(self, value: int):
        v = {"message_expiry": int(value)}
        self.setting = v

    @property
    def map_update_interval(self) -> int:
        return int(self.setting["map_update_interval"])

    @map_update_interval.setter
    def map_update_interval(self, value: int):
        v = {"map_update_interval": int(value)}
        self.setting = v

    @property
    def alarm_distance(self) -> int:
        return int(self.setting["alarm_distance"])

    @alarm_distance.setter
    def alarm_distance(self, value: int):
        v = {"alarm_distance": int(value)}
        self.setting = v

    @property
    def clipboard_check_interval(self) -> int:
        return int(self.setting["clipboard_check_interval"])

    @clipboard_check_interval.setter
    def clipboard_check_interval(self, value: int):
        v = {"clipboard_check_interval": int(value)}
        self.setting = v


if __name__ == "__main__":
    orig = 4000
    gs = GeneralSettings()
    gs.clipboard_check_interval = 20
    test = gs.background_color
    test = gs.test

    act = GeneralSettings().sound_active
    GeneralSettings().sound_active = not GeneralSettings().sound_active
    cparser = GeneralSettings().character_parser
    act = GeneralSettings().sound_active

    check = GeneralSettings().clipboard_check_interval
    cparser = GeneralSettings().character_parser
    newv = 200
    GeneralSettings().clipboard_check_interval = newv
    cparser = GeneralSettings().character_parser
    check = GeneralSettings().clipboard_check_interval
    print(check)
    GeneralSettings().clipboard_check_interval = orig
