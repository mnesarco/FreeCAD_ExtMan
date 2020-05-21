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
from freecad.extman import getResourcePath, isWindowsPlatform

class Components:
    def __init__(self, **comps):
        for k, v in comps.items():
            setattr(self, k, v)

def getResourceUrl(*path):
    
    """
    Translate path into (url, parentUrl, absPath)
    """
    
    filepath = getResourcePath('html', *path)
    parent = os.path.dirname(filepath)
    if isWindowsPlatform:
        url = filepath.replace('\\', '/')
        parentUrl = parent.replace('\\', '/')
    else:
        url = filepath
        parentUrl = parent
    return f"file://{url}", f"file://{parentUrl}", filepath

