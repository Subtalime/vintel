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

import os
import sys
import logging

LOGGER = logging.getLogger(__name__)

def resourcePath(relativePath=None):
    """ Get absolute path to resource, works for dev and for PyInstaller
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = os.path.dirname(sys.executable)
    else:
        basePath = os.path.join(os.path.abspath("."), "vi/ui/res")
    if not relativePath:
        return basePath
    returnpath = os.path.join(basePath, relativePath)
    return returnpath


def soundPath(relativePath=None):
    """ Get absolute path to resource, works for dev and for PyInstaller
    """
    basePath = resourcePath("sound")
    if not relativePath:
        return basePath
    returnpath = os.path.join(basePath, relativePath)
    return returnpath


def mapPath(relativePath=None):
    """ Get absolute path to resource, works for dev and for PyInstaller
    """
    basePath = resourcePath("mapdata")
    if not relativePath:
        return basePath
    returnpath = os.path.join(basePath, relativePath)
    return returnpath


def getEveDir() -> str:
    eveDirectory = None
    if sys.platform.startswith("darwin"):
        eveDirectory = os.path.join(os.path.expanduser("~"), "Documents", "EVE")
        if not os.path.exists(eveDirectory):
            eveDirectory = os.path.join(os.path.expanduser("~"), "Library", "Application Support",
                                        "Eve Online",
                                        "p_drive", "User", "My Documents", "EVE")
    elif sys.platform.startswith("linux"):
        eveDirectory = os.path.join(os.path.expanduser("~"), "EVE")
    elif sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, 5, 0, 0, buf)
        documentsPath = buf.value
        eveDirectory = os.path.join(documentsPath, "EVE")
    return eveDirectory


eveChatLogDir = None


def getEveChatlogDir(passedDir: str = None, log: bool = False) -> str:
    global eveChatLogDir
    if passedDir:
        eveChatLogDir = passedDir
    if eveChatLogDir:
        return eveChatLogDir
    eveDir = getEveDir()
    chatLogDirectory = os.path.join(eveDir, "logs", "Chatlogs")
    if log:
        LOGGER.debug("getEveChatlogDir: {}".format(chatLogDirectory))
    return chatLogDirectory


def getVintelDir(filePath: str = None, log: bool = False) -> str:
    eveDir = getEveDir()
    vintelDir = os.path.join(eveDir, "vintel")
    if not os.path.exists(vintelDir):
        try:
            os.makedirs(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelDir: Error creating \"%s\": %r" % (vintelDir, e))
            else:
                LOGGER.error("getVintelDir: Error creating \"%s\": %r", vintelDir, e)
    if filePath:
        vintelDir = os.path.join(vintelDir, filePath)
    return vintelDir


def getVintelLogDir(log: bool = False) -> str:
    vintelDir = os.path.join(getVintelDir(), "logs")
    if not os.path.exists(vintelDir):
        try:
            os.makedirs(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelLogDir: Error creating \"%s\": %r" % (vintelDir, e))
            else:
                LOGGER.error("getVintelLogDir: Error creating \"%s\": %r", vintelDir, e)
    return vintelDir


def getVintelMap(regionName: str = None, log: bool = False) -> str:
    vintelDir = mapPath()
    if not os.path.exists(vintelDir):
        try:
            os.makedirs(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelMap: Error creating \"%s\": %r", vintelDir, e)
            else:
                LOGGER.error("getVintelMap: Error creating \"%s\": %r", vintelDir, e)
    if regionName:
        if not regionName.endswith(".svg"):
            regionName += ".svg"
        vintelDir = os.path.join(vintelDir, regionName)
    return vintelDir


def getVintelSound(soundFile: str = None, log: bool = False) -> str:
    vintelDir = soundPath()
    if not os.path.exists(vintelDir):
        try:
            os.makedirs(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelSound: Error creating \"%s\": %r", vintelDir, e)
            else:
                LOGGER.error("getVintelSound: Error creating \"%s\": %r", vintelDir, e)
    if soundFile:
        if not soundFile.endswith(".wav"):
            soundFile += ".wav"
        vintelDir = os.path.join(vintelDir, soundFile)
    return vintelDir


def createResourceDirs(log: bool = False):
    getVintelDir(log=log)
    getVintelMap(log=log)
    getVintelSound(log=log)
    getVintelLogDir(log=log)
