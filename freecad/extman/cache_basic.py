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

import FreeCADGui as Gui

__CACHE__ = {} # Singleton

def clearCacheArea(name):
    global __CACHE__
    if name in __CACHE__:
        __CACHE__[name].clear()

def useCacheArea(areaName):

    def useCache(key, default=None):
        cached = __CACHE__[areaName].get(key, default)
        def setHook(value):
            __CACHE__[areaName][key] = value
        return (cached, setHook)

    def clearCache():
        clearCacheArea(areaName)

    if not areaName in __CACHE__:
        __CACHE__[areaName] = {}

    return (useCache, clearCache)
