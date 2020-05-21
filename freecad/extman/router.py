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

def Route(exact=None, prefix=None, func=None, pattern=None, anyOf=None):
    if exact:
        return lambda x: x == exact
    elif prefix:
        return lambda x: x.startswith(prefix)
    elif func: 
        return func
    elif pattern:
        return lambda x: pattern.match(x)
    elif anyOf:
        return lambda x: x in anyOf
    else:
        return lambda x: False

class Router:

    def __init__(self, **routes):
        self._CURRENT_ = '/'
        for k, match in routes.items():
            self.__setattr__("is{0}".format(k), self.dispatch(k, match))

    def getCurrent(self):
        return self._CURRENT_

    def dispatch(self, route, matcher):
        def fn():
            return matcher(self.getCurrent())
        return fn

    def setRoute(self, route):
        self._CURRENT_ = route
