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

import FreeCADGui as Gui

__CACHE__ = {}  # Singleton


def clear_cache_area(name):
    global __CACHE__
    if name in __CACHE__:
        __CACHE__[name].clear()


def use_cache_area(area_name):

    def use_cache(key, default=None):
        cached = __CACHE__[area_name].get(key, default)

        def set_hook(value):
            __CACHE__[area_name][key] = value

        return cached, set_hook

    def clear_cache():
        clear_cache_area(area_name)

    if area_name not in __CACHE__:
        __CACHE__[area_name] = {}

    return use_cache, clear_cache
