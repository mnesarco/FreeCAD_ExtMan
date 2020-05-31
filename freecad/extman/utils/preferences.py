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

# Parameter type and default mapping. 
# str parameter mapping required only if default value
# Constant
__PARAMETER_OPTIONS__ = {
    'UpdateCheck': (bool, True),
    'ProxyCheck': (str, 'none'),  # none, system, user
    'ProxyUrl': (str, ''),
    'PackagesViewMode': (str, 'rows'),  # rows, cards
    'CustomCloudSources': (str, '[]')
}

__PARAMETER_GROUP__ = "User parameter:BaseApp/Preferences/ExtMan"  # Constant


class ParametersProxy:

    def __init__(self):
        pass

    def __getattribute__(self, name):

        group = App.ParamGet(__PARAMETER_GROUP__)
        (param_type, param_default) = __PARAMETER_OPTIONS__.get(name, (str, ''))

        if param_type == str:
            return group.GetString(name, param_default)

        if param_type == bool:
            return group.GetBool(name, param_default)

        if param_type == int:
            return group.GetInt(name, param_default)

        if param_type == float:
            return group.GetFloat(name, param_default)

    def __setattr__(self, name, value):

        group = App.ParamGet(__PARAMETER_GROUP__)
        (param_type, _) = __PARAMETER_OPTIONS__.get(name, (str, ''))

        if param_type == str:
            return group.SetString(name, value)

        if param_type == bool:
            return group.SetBool(name, value)

        if param_type == int:
            return group.SetInt(name, value)

        if param_type == float:
            return group.SetFloat(name, value)


def set_plugin_parameter(plugin, name, value):
    param = App.ParamGet('User parameter:Plugins/{0}'.format(plugin))
    if isinstance(value, str):
        param.SetString(name, value)
    elif isinstance(value, bool):
        param.SetBool(name, value)
    elif isinstance(value, float):
        param.SetFloat(name, value)
    elif isinstance(value, int):
        param.SetInt(name, value)
    else:
        raise ValueError('Unsupported param type [{0}] {1}'.format(type(value), name))


# ExtMan Parameters Proxy (Constant/Singleton)
ExtManParameters = ParametersProxy()
