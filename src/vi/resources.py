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

import os
import sys
import logging
from vi.version import ROOT_DIR

LOGGER = logging.getLogger(__name__)


def get_resource_path(relative_path=None):
    """ Get absolute path to resource, works for dev and for PyInstaller
    """
    if getattr(sys, "frozen", False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.join(ROOT_DIR, "vi", "ui", "res")
    if relative_path:
        base_path = os.path.join(base_path, relative_path)
    LOGGER.debug(f"resourcePath is {base_path}")
    return base_path


def build_resource_path(resource_dir, relative_dir) -> str:
    base_path = get_resource_path(resource_dir)
    if relative_dir:
        base_path = os.path.join(base_path, relative_dir)
    return base_path


def get_sound_resource_path(relative_path=None):
    """ Get absolute path to resource, works for dev and for PyInstaller
    """
    return build_resource_path("sound", relative_path)


def get_map_resource_path(relative_path=None):
    """ Get absolute path to resource, works for dev and for PyInstaller
    """
    return build_resource_path("mapdata", relative_path)


def get_eve_directory() -> str:
    eve_directory = None
    if sys.platform.startswith("darwin"):
        eve_directory = os.path.join(os.path.expanduser("~"), "Documents", "EVE")
        if not os.path.exists(eve_directory):
            eve_directory = os.path.join(
                os.path.expanduser("~"),
                "Library",
                "Application Support",
                "Eve Online",
                "p_drive",
                "User",
                "My Documents",
                "EVE",
            )
    elif sys.platform.startswith("linux"):
        eve_directory = os.path.join(os.path.expanduser("~"), "EVE")
    elif sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
        import ctypes.wintypes

        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, 5, 0, 0, buf)
        eve_directory = os.path.join(buf.value, "EVE")
    return eve_directory


eve_chat_log_directory = None


def get_eve_chatlog_directory(passedDir: str = None, log: bool = False) -> str:
    global eve_chat_log_directory
    if passedDir:
        eve_chat_log_directory = passedDir
    if eve_chat_log_directory:
        return eve_chat_log_directory
    eve_dir = get_eve_directory()
    chat_log_directory = os.path.join(eve_dir, "logs", "Chatlogs")
    if log:
        LOGGER.debug("getEveChatlogDir: {}".format(chat_log_directory))
    return chat_log_directory


def get_vintel_directory(filePath: str = None, log: bool = False) -> str:
    eve_dir = get_eve_directory()
    vintel_dir = os.path.join(eve_dir, "vintel")
    if not os.path.exists(vintel_dir):
        try:
            os.makedirs(vintel_dir)
        except Exception as e:
            if not log:
                print('getVintelDir: Error creating "%s": %r' % (vintel_dir, e))
            else:
                LOGGER.error('getVintelDir: Error creating "%s": %r', vintel_dir, e)
    if filePath:
        vintel_dir = os.path.join(vintel_dir, filePath)
    return vintel_dir


def get_vintel_log_directory(log: bool = False) -> str:
    vintel_dir = os.path.join(get_vintel_directory(), "logs")
    if not os.path.exists(vintel_dir):
        try:
            os.makedirs(vintel_dir)
        except Exception as e:
            if not log:
                print('getVintelLogDir: Error creating "%s": %r' % (vintel_dir, e))
            else:
                LOGGER.error('getVintelLogDir: Error creating "%s": %r', vintel_dir, e)
    return vintel_dir


def get_vintel_map_directory(use_logger: bool = False) -> str:
    vintel_dir = get_map_resource_path()
    if not os.path.exists(vintel_dir):
        try:
            os.makedirs(vintel_dir)
        except Exception as e:
            if not use_logger:
                print('getVintelMap: Error creating "%s": %r', vintel_dir, e)
            else:
                LOGGER.error('getVintelMap: Error creating "%s": %r', vintel_dir, e)
    return vintel_dir


def get_vintel_map_file_path(region_name: str = None, log: bool = False) -> str:
    vintel_dir = get_vintel_map_directory(log)
    if region_name:
        if not region_name.endswith(".svg"):
            region_name += ".svg"
        vintel_dir = os.path.join(vintel_dir, region_name)
    return vintel_dir


def get_vintel_sound_file_path(sound_file: str = None, log: bool = False) -> str:
    vintel_dir = get_sound_resource_path()
    if not os.path.exists(vintel_dir):
        try:
            os.makedirs(vintel_dir)
        except Exception as e:
            if not log:
                print('getVintelSound: Error creating "%s": %r', vintel_dir, e)
            else:
                LOGGER.error('getVintelSound: Error creating "%s": %r', vintel_dir, e)
    if sound_file:
        if not sound_file.endswith(".wav"):
            sound_file += ".wav"
        vintel_dir = os.path.join(vintel_dir, sound_file)
    return vintel_dir


def createResourceDirs(log: bool = False):
    get_vintel_directory(log=log)
    get_vintel_map_file_path(log=log)
    get_vintel_sound_file_path(log=log)
    get_vintel_log_directory(log=log)
