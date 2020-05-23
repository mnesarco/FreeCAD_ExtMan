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

import FreeCAD as App
import FreeCADGui as Gui
import functools
import os
from PySide import QtGui

ADDON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))  # Constant
isWindowsPlatform = os.path.sep == '\\'  # Constant


def log(*msg):
    """Prints to FreeCAD Console"""
    App.Console.PrintLog("[ExtMan] {0}\n".format(' '.join(msg)))


def log_err(*msg):
    """Prints to FreeCAD Console"""
    App.Console.PrintError("[ExtMan] {0}\n".format(' '.join(msg)))


def get_resource_path(*paths, create_dir=False):
    """Returns a path inside Resources"""
    path = os.path.join(ADDON_DIR, 'Resources', *paths)
    if create_dir and not os.path.exists(path):
        os.makedirs(path)
    return path


# Setup translations
try:
    Gui.addLanguagePath(get_resource_path('translations'))
    Gui.updateLocale()
except Exception as ex:
    log('Translation loading error')


# Define tr
try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    @functools.lru_cache()
    def tr(text):
        """Translate text"""
        u = QtGui.QApplication.translate('extman', text, None, _encoding)
        return u.replace(chr(39), "&rsquo;")

except Exception as ex:
    @functools.lru_cache()
    def tr(text):
        """Translate text"""
        u = QtGui.QApplication.translate('extman', text, None)
        return u.replace(chr(39), "&rsquo;")


# Ensure Mod dir
if not os.path.exists(os.path.join(App.getUserAppDataDir(), 'Mod')):
    os.makedirs(os.path.join(App.getUserAppDataDir(), 'Mod'))


# Ensure Macro dir
if not os.path.exists(os.path.join(App.getUserMacroDir(True))):
    os.makedirs(App.getUserMacroDir(True))

