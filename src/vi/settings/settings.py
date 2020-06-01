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
import os
from vi.cache import Cache
from vi.states import State
import pickle
from vi.resources import soundPath


class _Settings:
    ship_parser: bool = False
    character_parser: bool = False

    def __init__(self):
        self.cache = Cache()
        self._config = {}
        self.KEY = "GENERAL"
        res = self.cache.fetch("my_settings", outdated=True)
        if res:
            self._config = pickle.loads(res)
        self.defaults = {}

    def _set_property(self, key, value):
        self._config[key] = value
        self.cache.put("my_settings", pickle.dumps(self._config))

    def _get_property(self, property_name):
        try:
            return self._config[property_name]
        except KeyError:
            return None

    @property
    def setting(self):
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
        self._set_property(self.KEY, value)


class RegionSettings(_Settings):
    def __init__(self):
        super().__init__()
        self.KEY = "regions"
        self.defaults = {
            "region_names": "delve,querious",
            "selected": "delve",
            "jump_bridge_url": None,
            "jump_bridge_data": None,
        }

    @property
    def selected_region(self) -> str:
        return self.setting["selected"]

    @selected_region.setter
    def selected_region(self, value: str):
        v = {"selected": value}
        self.setting = v

    @property
    def region_names(self) -> str:
        return self.setting["region_names"]

    @region_names.setter
    def region_names(self, value: str):
        v = {"region_names": value}
        self.setting = v

    @property
    def jump_bridge_url(self):
        return self.setting["jump_bridge_url"]

    @jump_bridge_url.setter
    def jump_bridge_url(self, value: str):
        v = {"jump_bridge_url": value}
        self.setting = v

    @property
    def jump_bridge_data(self):
        return self.setting["jump_bridge_data"]

    @jump_bridge_data.setter
    def jump_bridge_data(self, value: str):
        v = {"jump_bridge_data": value}
        self.setting = v


class ColorSettings(_Settings):
    def __init__(self):
        super().__init__()
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
        return self.setting["js_alarm_colors"]

    @js_alarm_colors.setter
    def js_alarm_colors(self, value: dict):
        v = {"js_alarm_colors": value}
        self.setting = v


class ChatroomSettings(_Settings):
    def __init__(self):
        super().__init__()
        self.KEY = "chatroom"
        self.defaults = {"room_names": "querius.imperium,delve.imperium"}

    @property
    def room_names(self) -> str:
        return self.setting["room_names"]

    @room_names.setter
    def room_names(self, value: str):
        v = {"room_names": value}
        self.setting = v


class SoundSettings(_Settings):
    def __init__(self):
        super().__init__()
        self.KEY = "sound"
        self._defaults()

    def _defaults(self):
        listing = []
        for distance in range(0, 6):
            entry = [
                "{} Jumps".format(distance),
                os.path.join(soundPath(), "alert.wav"),
                25,
            ]
            listing.append(entry)
        listing.append(["KOS", os.path.join(soundPath(), "warning.wav"), 25])
        listing.append(["Request", os.path.join(soundPath(), "request.wav"), 25])
        self.defaults["sound"] = listing

    @property
    def sound(self):
        return self.setting["sound"]

    @sound.setter
    def sound(self, value):
        v = {"sound": value}
        self.setting = v


class GeneralSettings(_Settings):
    def __init__(self):
        super().__init__()
        self.KEY = "general"
        self.defaults = {
            "message_expiry": 20 * 60,
            "clipboard_check_interval": 4 * 1000,
            "ship_parser_enabled": False,
            "character_parser_enabled": True,
            "self_notify": True,
            "popup_notification": True,
            "alarm_distance": 2,
            "background_color": "#c6d9ec",
            "map_update_interval": 4 * 1000,
            "sound_active": True,
            "show_requests": True,
            "log_level": 10,
        }

    @property
    def sound_active(self) -> bool:
        return self.setting["sound_active"]

    @sound_active.setter
    def sound_active(self, value: bool):
        v = {"sound_active": value}
        self.setting = v

    @property
    def log_level(self) -> int:
        return self.setting["log_level"]

    @log_level.setter
    def log_level(self, value: int):
        v = {"log_level": value}
        self.setting = v

    @property
    def show_requests(self) -> bool:
        return self.setting["show_requests"]

    @show_requests.setter
    def show_requests(self, value: bool):
        v = {"show_requests": value}
        self.setting = v

    @property
    def character_parser(self) -> bool:
        return self.setting["character_parser_enabled"]

    @character_parser.setter
    def character_parser(self, value: bool):
        v = {"character_parser_enabled": value}
        self.setting = v

    @property
    def ship_parser(self) -> bool:
        return self.setting["ship_parser_enabled"]

    @ship_parser.setter
    def ship_parser(self, value: bool):
        v = {"ship_parser_enabled": value}
        self.setting = v

    @property
    def popup_notification(self) -> bool:
        return self.setting["popup_notification"]

    @popup_notification.setter
    def popup_notification(self, value: bool):
        v = {"popup_notification": value}
        self.setting = v

    @property
    def self_notify(self) -> bool:
        return self.setting["self_notify"]

    @self_notify.setter
    def self_notify(self, value: bool):
        v = {"self_notify": value}
        self.setting = v

    @property
    def background_color(self) -> str:
        return self.setting["background_color"]

    @background_color.setter
    def background_color(self, value: str):
        v = {"background_color": value}
        self.setting = v

    @property
    def message_expiry(self) -> int:
        return self.setting["message_expiry"]

    @message_expiry.setter
    def message_expiry(self, value: int):
        v = {"message_expiry": value}
        self.setting = v

    @property
    def map_update_interval(self) -> int:
        return self.setting["map_update_interval"]

    @map_update_interval.setter
    def map_update_interval(self, value: int):
        v = {"map_update_interval": value}
        self.setting = v

    @property
    def alarm_distance(self) -> int:
        return self.setting["alarm_distance"]

    @alarm_distance.setter
    def alarm_distance(self, value: int):
        v = {"alarm_distance": value}
        self.setting = v

    @property
    def clipboard_check_interval(self) -> int:
        return self.setting["clipboard_check_interval"]

    @clipboard_check_interval.setter
    def clipboard_check_interval(self, value: int):
        v = {"clipboard_check_interval": value}
        self.setting = v


if __name__ == "__main__":
    orig = 4000
    check = GeneralSettings().clipboard_check_interval
    newv = 200
    GeneralSettings().clipboard_check_interval = newv
    check = GeneralSettings().clipboard_check_interval
    print(check)
    GeneralSettings().clipboard_check_interval = orig
