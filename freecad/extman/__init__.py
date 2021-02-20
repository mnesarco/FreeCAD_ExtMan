# -*- coding: utf-8 -*-
# ***************************************************************************
# *                                                                         *
# *  Copyright (c) 2020 Frank Martinez <mnesarco at gmail.com>              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *  This program is distributed in the hope that it will be useful,        *
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
# *  GNU General Public License for more details.                           *
# *                                                                         *
# *  You should have received a copy of the GNU General Public License      *
# *  along with this program.  If not, see <https://www.gnu.org/licenses/>. *
# *                                                                         *
# ***************************************************************************

import functools
from pathlib import Path

import FreeCAD as App
from PySide import QtGui


def log(*msg):
    """Prints to FreeCAD Console"""
    App.Console.PrintLog("[ExtMan] {0}\n".format(' '.join((str(i) for i in msg))))


def log_err(*msg):
    """Prints to FreeCAD Console"""
    App.Console.PrintError("[ExtMan] {0}\n".format(' '.join((str(i) for i in msg))))


def get_resource_path(*paths, create_dir=False):
    """Returns a path inside resources"""
    path = Path(__extman_home_path__, 'resources', *paths)
    if create_dir and not path.exists():
        path.mkdir(parents=True)
    return path


def get_macro_path():
    """Returns platform independent macro base path"""
    return Path(App.getUserMacroDir(True))


def get_mod_path():
    """Returns platform independent user mod base path"""
    return __user_mod_path__


def get_app_data_path():
    """Returns platform independent user app data path"""
    return __user_appdata_path__


def get_cache_path():
    """Returns platform independent cache path"""
    return __extman_cache_path__


def get_freecad_home_path():
    """Returns platform independent freecad install path"""
    return __freecad_home_path__


def get_freecad_resource_path():
    """Returns platform independent freecad resource path"""
    return __freecad_resource_path__


# +---------------------------------------------------------------------------+
# | Translations setup                                                        |
# +---------------------------------------------------------------------------+

tr_initialized = False
tr_encoding = None

def setup_translation():
    import FreeCADGui as Gui
    global tr_encoding

    try:
        Gui.addLanguagePath(get_resource_path('translations'))
        Gui.updateLocale()
    except Exception as ex:
        log('Translation loading error')


@functools.lru_cache()
def tr(text):
    """Translate text"""
    if tr_encoding:
        u = QtGui.QApplication.translate('extman', text, None, tr_encoding)
    else:
        u = QtGui.QApplication.translate('extman', text, None)
    return u.replace(chr(39), "&rsquo;")


# +---------------------------------------------------------------------------+
# | Base paths setup                                                          |
# +---------------------------------------------------------------------------+

__freecad_home_path__ = Path(App.getHomePath()).resolve()
__freecad_resource_path__ = Path(App.getResourceDir())
__extman_home_path__ = Path(__file__).parent
__user_appdata_path__ = Path(App.getUserAppDataDir())
__user_mod_path__ = Path(__user_appdata_path__, 'Mod')
__extman_cache_path__ = Path(__user_appdata_path__, 'ExtManCache')

# Ensure Mod dir
if not __user_mod_path__.exists():
    __user_mod_path__.mkdir(parents=True)


# Ensure Macro dir
if not get_macro_path().exists():
    get_macro_path().mkdir(parents=True)


# Ensure Cache dir
if not __extman_cache_path__.exists():
    __extman_cache_path__.mkdir(parents=True)

