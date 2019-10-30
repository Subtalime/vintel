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

def getEveChatlogDir() -> str:
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
    return chatLogDirectory

def getVintelDir() -> str:
    eveDir = getEveChatlogDir()
    vintelDir = os.path.join(os.path.dirname(os.path.dirname(eveDir)), "vintel")
    return vintelDir
