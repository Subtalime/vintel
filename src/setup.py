#   Vintel - Visual Intel Chat Analyzer
#   Copyright (c) 2019. Steven Tschache (github@tschache.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.	 If not, see <http://www.gnu.org/licenses/>.
#
#

from cx_Freeze import setup, Executable
import os
import sys
from vi.version import VERSION, DISPLAY, AUTHOR, AUTHOR_EMAIL, URL, PROGNAME
from vi.resources import resourcePath

if sys.platform == "win32":
    base = "Win32GUI"
executables = [Executable("vintel.py", base=base, icon="icon.ico")]
include_files = [
    # os.path.join(sys.base_prefix, 'DLLs', 'sqlite3.dll'),
    os.path.join(sys.base_prefix, 'DLLs', "tcl86t.dll"),
    os.path.join(sys.base_prefix, 'DLLs', "tk86t.dll"),
    ('vi/ui/res/mapdata/Delve.svg', "mapdata/Delve.svg"),
    ('vi/ui/res/mapdata/Querious.svg', "mapdata/Querious.svg"),
    ("vi/ui/res/sound/warning.wav", "sound/warning.wav"),
    ("vi/ui/res/sound/request.wav", "sound/request.wav"),
    ("vi/ui/res/sound/alert.wav", "sound/alert.wav"),
    ("vi/ui/res/logo.png", "logo.png"),
    ("vi/ui/res/logo_small.png", "logo_small.png"),
    ("vi/ui/res/logo_small_green.png", "logo_small_green.png"),
    ("vi/ui/res/qmark.png", "qmark.png"),
    ("vi/ui/res/logging.yaml", "logging.yaml.example"),
    ("docs/regionselect.txt", "docs/regionselect.txt"),
    ("docs/jumpbridgeformat.txt", "docs/jumpbridgeformat.txt"),
]
requires = ['requests', "PyQt5", "pyqtwebengine", "pyglet", 'beautifulsoup4', 'six', 'packaging', 'clipboard', 'esipy',
            'pyswagger',
            'PyYAML']
packages = []
packages = ["esipy", "pyswagger", "pyglet", "six", "clipboard"]

replace_paths = [("vi/ui/res/mapdata", "mapdata"), ("vi/ui/res", "sound")]
setup(
    name=PROGNAME,
    version=VERSION,
    description=DISPLAY,
    executables=executables,
    options={
        'build_exe': {
            'build_exe': "../releases/packages/Vintel-" + str(VERSION),
            'packages': packages,
            'include_files': include_files,
            'replace_paths': replace_paths,
        }
    },
    requires=requires,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
)
