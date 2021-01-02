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
import zipfile
from vi.version import VERSION, DISPLAY, AUTHOR, AUTHOR_EMAIL, URL, PROGNAME
from vi.resources import resourcePath

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
release_dir = "releases"
destination = os.path.join(base_dir, release_dir, "packages")
setup_dir = os.path.join(base_dir, release_dir, "setup")

if not os.path.exists(destination):
    os.makedirs(destination)
if not os.path.exists(setup_dir):
    os.makedirs(setup_dir)

base = None
if sys.platform == "win32":
    base = "Win32GUI"

# clean up previous builds
folders = ["dist", "build"]
folders = ["dist", ]
for folder in folders:
    if os.path.exists(folder):
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except FileNotFoundError:
                pass

executables = [
    Executable(
        "vintel.py",
        base=base,
        icon="icon.ico",
        shortcutName="Vintel",
        shortcutDir="DesktopFolder",
    )
]

move_files = (
    ("mapdata",),
    ("sound", ),
    ("docs", ),
    ("logo.png",),
    ("logo_small_green.png",),
    ("logo_small.png",),
    ("qmark.png",),
    ("logging.yaml", "logging.yaml.example"),
)

include_files = [
    os.path.join(sys.base_prefix, "DLLs", "tcl86t.dll"),
    os.path.join(sys.base_prefix, "DLLs", "tk86t.dll"),
    # ("logging.yaml", "logging.yaml.example"),
    ("docs/regionselect.txt", "docs/regionselect.txt"),
    ("docs/jumpbridgeformat.txt", "docs/jumpbridgeformat.txt"),
    (os.path.join(base_dir, "README.md"), "README.md"),
]

for pack in move_files:
    src = pack[0]
    if len(pack) == 1:
        dest = pack[0]
    else:
        dest = pack[1]
    include_files.append((os.path.join(resourcePath(), src), dest))

install_requires = [
    "requests",
    "PyQt5",
    "pyqtwebengine",
    "pyglet",
    "beautifulsoup4",
    "six",
    "packaging",
    "clipboard",
    "esipy",
    "pyswagger",
    "PyYAML",
    "colour",
    # "stopwatch",
    # "zroya",
]
packages = ["pyqt5", "esipy", "pyswagger", "pyglet", "six", "clipboard"]

replace_paths = [
    (os.path.join(resourcePath(), "mapdata"), "mapdata"),
    (os.path.join(resourcePath(), "sound"), "sound"),
    (os.path.join(resourcePath(), "docs"), "docs"),
    ("src/vi/ui/res", "."),  # README.md
]

build_exe_options = {
    "build_exe": "{}/Vintel-{}".format(destination, str(VERSION)),
    "packages": packages,
    "include_files": include_files,
    "replace_paths": replace_paths,
    "includes": "atexit",
}
bdist_msi_options = {
    "install_icon": "icon.ico",
    "product_code": "{A34EE3A5-832B-4E7A-8FCE-71DDC4BC7E1B}",
    "upgrade_code": "{A34EE3A5-832B-4E7A-8FCE-71DDC4BC7E1C}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\%s\%s" % (PROGNAME, PROGNAME),
}

try:
    setup(
        name=PROGNAME,
        version=VERSION,
        description=DISPLAY,
        executables=executables,
        options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options, },
        requires=install_requires,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,
    )
except Exception as e:
    print("Setup-Exception")
    print(e)

try:
    for file in os.listdir("dist"):
        shutil.copy(os.path.join("dist", file), setup_dir)
except FileNotFoundError:
    pass


# create ZIP archive
def zip_it_up(path, zipf):
    for root, dirs, files in os.walk(path):
        for file_name in files:
            zipf.write(os.path.join(root, file_name))


try:
    program_name = "{}-{}".format(PROGNAME, VERSION)
    if os.path.isfile(os.path.join(destination, program_name + ".zip")):
        os.remove(os.path.join(destination, program_name + ".zip"))
    package_path = os.path.join(destination, program_name)
    zip_path = package_path + ".zip"
    zip_file = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
    zip_it_up(package_path, zip_file)
    zip_file.close()
except Exception as e:
    raise e
