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
#
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
#

from cx_Freeze import setup, Executable
import os
import sys

if sys.platform == "win32":
    base = "Win32GUI"
executables = [Executable("vintel.py", base=base, icon="icon.ico")]
include_files = [os.path.join(sys.base_prefix, 'DLLs', 'sqlite3.dll'), "vi/dotlan"]
packages = []
setup(
    name="Vintel",
    version = "1.0",
    description = "Description",
    executables = executables,
    options = {
        'build_exe': {
            'packages': packages,
            'include_files': include_files
        }
    },
    requires=['requests', "pyqt5", 'beautifulsoup4', 'six', 'packaging', 'clipboard', 'esipy', 'pyswagger']
)
