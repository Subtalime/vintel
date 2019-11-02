from setuptools import find_packages
from cx_Freeze import setup, Executable

import sys

base = None

if sys.platform == "win32":
    base = "Win32GUI"

import os.path

PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')

executables = [Executable("vintel.py", base=base, icon="icon.ico")]

packages = ["idna", "appdirs", "packaging.version", "packaging.specifiers", "packaging", "pyglet", "pyqt5", "pyttsx3"]

package_data = {'ui': ['vi/ui/*'], "sound": ["sound"]}

options = {
    'build_exe': {
        'packages': packages,
        # 'include_files': [
        #     os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tk86t.dll'),
        #     os.path.join(PYTHON_INSTALL_DIR, 'DLLs', 'tcl86t.dll'),
        # ],

    },
}

setup(
    name="VINTEL",
    options=options,
    version="2.0.0",
    description='EVE-Online Intel chat analyzer',
    executables=executables,
    include_package_data=True,
    package_data={'': ['*.ui', '*.png', '*.svg', '*.wav']},
)
