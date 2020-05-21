# -*- coding: utf-8 -*-
#***************************************************************************
#*                                                                         *
#*  Copyright (c) 2020 Frank Martinez <mnesarco at gmail.com>              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*  This program is distributed in the hope that it will be useful,        *
#*  but WITHOUT ANY WARRANTY; without even the implied warranty of         *
#*  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
#*  GNU General Public License for more details.                           *
#*                                                                         *
#*  You should have received a copy of the GNU General Public License      *
#*  along with this program.  If not, see <https://www.gnu.org/licenses/>. *
#*                                                                         *
#***************************************************************************

import os
import FreeCADGui as Gui
import FreeCAD as App
import functools
from PySide import QtGui

ADDON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # Constant
isWindowsPlatform = os.path.sep == '\\' # Constant

def log(*msg):
    App.Console.PrintLog("[ExtMan] {0}\n".format(' '.join(msg)))

def getResourcePath(*paths, createDir=False):
    path = os.path.join(ADDON_DIR, 'Resources', *paths)
    if createDir and not os.path.exists(path):
        os.makedirs(path)
    return path

try:
    Gui.addLanguagePath(":/translations")
    Gui.updateLocale()
except:
    log('Translation loading error')

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    @functools.lru_cache()
    def tr(text):
        u = QtGui.QApplication.translate('extman', text, None, _encoding)
        return u.replace(chr(39), "&rsquo;")       
except:
    @functools.lru_cache()
    def tr(text):
        u = QtGui.QApplication.translate('extman', text, None)
        return u.replace(chr(39), "&rsquo;")       

