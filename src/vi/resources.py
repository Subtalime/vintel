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

def getEveChatlogDir(log: bool=False) -> str:
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
        logging.debug("getEveChatlogDir: {}".format(chatLogDirectory))
    return chatLogDirectory

def getVintelDir(filePath: str=None, log: bool=False) -> str:
    eveDir = getEveChatlogDir(log)
    vintelDir = os.path.join(os.path.dirname(os.path.dirname(eveDir)), "vintel")
    if not os.path.exists(vintelDir):
        try:
            os.mkdir(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelDir: Error creating \"%s\": %r", vintelDir, e)
            else:
                logging.error("getVintelDir: Error creating \"%s\": %r", vintelDir, e)
    if filePath:
        vintelDir = os.path.join(vintelDir, filePath)
    return vintelDir

def getVintelMap(regionName: str=None, log: bool=False) -> str:
    eveDir = getEveChatlogDir()
    vintelDir = os.path.join(os.path.dirname(os.path.dirname(eveDir)), "vintel", "mapdata")
    if not os.path.exists(vintelDir):
        try:
            os.mkdir(vintelDir)
        except Exception as e:
            if not log:
                print("getVintelMap: Error creating \"%s\": %r", vintelDir, e)
            else:
                logging.error("getVintelMap: Error creating \"%s\": %r", vintelDir, e)
    if regionName:
        if not regionName.endswith(".svg"):
            regionName += ".svg"
        vintelDir = os.path.join(vintelDir, regionName)
    return vintelDir
