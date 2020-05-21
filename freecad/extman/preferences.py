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

import FreeCAD as App

#------------------------------------------------------------------------------
# Parameter type and default mapping. 
# str parameter mapping required only if default value
__PARAMETER_OPTIONS__ = {
    'updateCheck': (bool, True),
    'proxyCheck': (int, 0), 
    'packagesViewMode': (str, 'rows')
}

__PARAMETER_GROUP__ = "User parameter:BaseApp/Preferences/ExtMan"

#------------------------------------------------------------------------------
class ParametersProxy:

    def __getattribute__(self, name):

        group = App.ParamGet(__PARAMETER_GROUP__)
        (ptype, pdefault) = __PARAMETER_OPTIONS__.get(name, (str, ''))        

        if ptype == str:
            return group.GetString(name, pdefault)

        if ptype == bool:
            return group.GetBool(name, pdefault)            

        if ptype == int:
            return group.GetInt(name, pdefault)                        

        if ptype == float:
            return group.GetFloat(name, pdefault)

    def __setattr__(self, name, value):
        
        group = App.ParamGet(__PARAMETER_GROUP__)
        (ptype, _) = __PARAMETER_OPTIONS__.get(name, (str, ''))        

        if ptype == str:
            return group.SetString(name, value)

        if ptype == bool:
            return group.SetBool(name, value)            

        if ptype == int:
            return group.SetInt(name, value)                        

        if ptype == float:
            return group.SetFloat(name, value)

#------------------------------------------------------------------------------
# ExtMan Parameters Proxy
ExtManParameters = ParametersProxy()

#------------------------------------------------------------------------------
def setPluginParam(plugin, name, value):
    param = App.ParamGet(f'User parameter:Plugins/{plugin}')
    if isinstance(value, str):
        param.SetString(name, value)
    elif isinstance(value, bool):
        param.SetBool(name, value)        
    elif isinstance(value, float):
        param.SetFloat(name, value)                        
    elif isinstance(value, int):
        param.SetInt(name, value)                
    else:
        raise ValueError(f'Unsupported param type [{type(value)}] {name}')