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

logger = logging.getLogger(__name__)
def resourcePath(relativePath):
    """ Get absolute path to resource, works for dev and for PyInstaller
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = sys._MEIPASS
    else:
        basePath = os.path.abspath(".")
    returnpath = os.path.join(basePath, relativePath)
    return returnpath

def soundPath(relativePath = None):
    """ Get absolute path to resource, works for dev and for PyInstaller
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = os.path.join(sys._MEIPASS, "sound")
    else:
        basePath = os.path.abspath("./sound")
    if relativePath:
        returnpath = os.path.join(basePath, relativePath)
    else:
        returnpath = basePath
    return returnpath

eveChatLogDir = None
def getEveChatlogDir(passedDir: str=None, log: bool=False) -> str:
    global eveChatLogDir
    if passedDir:
        eveChatLogDir = passedDir
    if eveChatLogDir:
        return passedDir

    if sys.platform.startswith("darwin"):
        chatLogDirectory = os.path.join(os.path.expanduser("~"), "Documents", "EVE", "logs", "Chatlogs")
        if not os.path.exists(chatLogDirectory):
            chatLogDirectory = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Eve Online",
                                            "p_drive", "User", "My Documents", "EVE", "logs", "Chatlogs")
    elif sys.platform.startswith("linux"):
        chatLogDirectory = os.path.join(os.path.expanduser("~"), "EVE", "logs", "Chatlogs")
    elif sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
        import ctypes.wintypes
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, 5, 0, 0, buf)
        documentsPath = buf.value
        chatLogDirectory = os.path.join(documentsPath, "EVE", "logs", "Chatlogs")
    if log:
        logger.debug("getEveChatlogDir: {}".format(chatLogDirectory))
    return chatLogDirectory

def getVintelLogDir(log: bool=False) -> str:
    vintelDir = getVintelDir()
    vintelDir = os.path.join(vintelDir, "logs")
    if not os.path.exists(vintelDir):
        try:
            os.makedirs(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelLogDir: Error creating \"%s\": %r" % (vintelDir, e))
            else:
                logger.error("getVintelLogDir: Error creating \"%s\": %r", vintelDir, e)
    return vintelDir

def getVintelDir(filePath: str=None, log: bool=False) -> str:
    eveDir = getEveChatlogDir(log)
    vintelDir = os.path.join(os.path.dirname(os.path.dirname(eveDir)), "vintel")
    if not os.path.exists(vintelDir):
        try:
            os.makedirs(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelDir: Error creating \"%s\": %r" % (vintelDir, e))
            else:
                logger.error("getVintelDir: Error creating \"%s\": %r", vintelDir, e)
    if filePath:
        vintelDir = os.path.join(vintelDir, filePath)
    return vintelDir

def getVintelMap(regionName: str=None, log: bool=False) -> str:
    getEveChatlogDir()
    vintelDir = os.path.join(getVintelDir(), "mapdata")
    if not os.path.exists(vintelDir):
        try:
            os.makedirs(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelMap: Error creating \"%s\": %r", vintelDir, e)
            else:
                logger.error("getVintelMap: Error creating \"%s\": %r", vintelDir, e)
    if regionName:
        if not regionName.endswith(".svg"):
            regionName += ".svg"
        vintelDir = os.path.join(vintelDir, regionName)
    return vintelDir

def getVintelSound(soundFile: str=None, log: bool=False) -> str:
    getEveChatlogDir()
    vintelDir = os.path.join(getVintelDir(), "sound")
    if not os.path.exists(vintelDir):
        try:
            os.makedirs(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelSound: Error creating \"%s\": %r", vintelDir, e)
            else:
                logger.error("getVintelSound: Error creating \"%s\": %r", vintelDir, e)
    if soundFile:
        if not soundFile.endswith(".wav"):
            soundFile += ".wav"
        vintelDir = os.path.join(vintelDir, soundFile)
    return vintelDir

def createResourceDirs(log: bool=False):
    getVintelDir(log=log)
    getVintelMap(log=log)
    getVintelSound(log=log)
    getVintelLogDir(log=log)
