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
import shutil
from vi.version import VERSION, DISPLAY, AUTHOR, AUTHOR_EMAIL, URL, PROGNAME
from vi.resources import resourcePath

destination = "../releases/packages"

if not os.path.exists(destination):
    os.makedirs(destination)

if sys.platform == "win32":
    base = "Win32GUI"

package_dir = "../releases/packages"
setup_dir = "../releases/setup"

for file in os.listdir("dist"):
    os.remove(os.path.join("dist", file))

executables = [Executable("vintel.py", base=base, icon="icon.ico")]

move_files = ((os.path.join('mapdata', 'Delve.svg'),),
              (os.path.join('mapdata', 'Querious.svg'),),
              (os.path.join('mapdata', 'Providencecatch.svg'),),
              (os.path.join('sound', 'warning.wav'),),
              (os.path.join('sound', 'request.wav'),),
              (os.path.join('sound', 'alert.wav'),),
              ('logo.png',),
              ('logo_small_green.png',),
              ('logo_small.png',),
              ('qmark.png',),
              ('logging.yaml', 'logging.yaml.example'),
              )

include_files = [
    os.path.join(sys.base_prefix, 'DLLs', "tcl86t.dll"),
    os.path.join(sys.base_prefix, 'DLLs', "tk86t.dll"),
    ("vi/ui/res/logging.yaml", "logging.yaml.example"),
    # ("docs/regionselect.txt", "docs/regionselect.txt"),
    ("docs/jumpbridgeformat.txt", "docs/jumpbridgeformat.txt"),
]
for pack in move_files:
    src = pack[0]
    if len(pack) == 1:
        dest = pack[0]
    else:
        dest = pack[1]
    include_files.append((os.path.join(resourcePath(), src), dest))

requires = ['requests', "PyQt5", "pyqtwebengine", "pyglet", 'beautifulsoup4', 'six', 'packaging',
            'clipboard', 'esipy',
            'pyswagger',
            'PyYAML']
packages = []
requires = ['requests', "PyQt5", "pyqtwebengine", "pyglet", 'beautifulsoup4', 'six', 'packaging', 'clipboard', 'esipy',
            'pyswagger', 'PyYAML']
packages = ["esipy", "pyswagger", "pyglet", "six", "clipboard"]
replace_paths = [(os.path.join(resourcePath(), "mapdata"), "mapdata"),
                 (os.path.join(resourcePath(), "sound"), "sound")]

build_exe_options = {
    'build_exe': "{}/Vintel-{}".format(package_dir, str(VERSION)),
    'packages': packages,
    'include_files': include_files,
    'replace_paths': replace_paths,
    'includes': 'atexit',
}

bdist_msi_options = {
    'install_icon': "icon.ico",
    'product_code': '{A34EE3A5-832B-4E7A-8FCE-71DDC4BC7E1B}',
    'upgrade_code': '{A34EE3A5-832B-4E7A-8FCE-71DDC4BC7E1C}',
    'add_to_path': False,
    'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % (PROGNAME, PROGNAME),
}

setup(
    name=PROGNAME,
    version=VERSION,
    description=DISPLAY,
    executables=executables,
    options={
        'build_exe': build_exe_options,
        'bdist_msi': bdist_msi_options,
    },
    requires=requires,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
)

replace_paths = [(os.path.join(resourcePath(), "mapdata"), "mapdata"),
                 (os.path.join(resourcePath(), "sound"), "sound")]
try:
    setup(
        name=PROGNAME,
        version=VERSION,
        description=DISPLAY,
        executables=executables,
        options={
            'build_exe': {
                'build_exe': os.path.join(destination, "Vintel-" + str(VERSION)),
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
except Exception as e:
    print(e)

for file in os.listdir("dist"):
    shutil.copy(os.path.join("dist", file), setup_dir)
    # shutil.move(os.path.join("dist", file), setup_dir)
