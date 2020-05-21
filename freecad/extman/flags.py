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

import functools, itertools
import json
from freecad.extman import tr, getResourcePath

@functools.lru_cache()
def getFlagsDatabase():

    """
    Reads Resources/data/flags.json
    returns dict( "{pkg.type:pkg.name.lower()}" => flags )
    """

    db = {}
    with open(getResourcePath('data', 'flags.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
        for flagId, flag in data.items():
            mods = flag.get('Mod', [])
            macros = flag.get('Macro', [])
            items = itertools.chain( ((m, 'Mod') for m in mods), ((m, 'Macro') for m in macros) )
            for name, mtype in items:
                key = "{0}:{1}".format(mtype, name.lower())
                mod = db.get(key, {})
                mod[flagId] = True
                db[key] = mod
    return db

def applyPredefinedFlags(pkg):
    ptype = pkg.type
    if ptype == 'Workbench':
        ptype = 'Mod'
    flags = getFlagsDatabase().get("{0}:{1}".format(ptype, pkg.name.lower()), [])
    if flags:
        if pkg.flags:
            pkg.flags.update(flags)
        else:
            pkg.flags = flags
    return pkg
