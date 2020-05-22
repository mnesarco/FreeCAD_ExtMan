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
import os
import re
import shutil

COMMA_SEP_LIST_PATTERN = re.compile(r'\s*,\s*', re.S)


def is_python_lib_available(name):
    try:
        __import__(name.strip())
        return True
    except:
        return False


def is_workbench_available(name, keys=None):
    if not keys:
        keys = Gui.listWorkbenches().keys()
    name = name.strip()
    return name in keys or (name + "Workbench") in keys


def is_executable_available(name):
    return bool(shutil.which(name))


def check_dependencies(manifest):
    """
    Check if dependencies are met

    Argiments:
        ExtensionManifest -- manifest
    Returns:
        tuple -- (passed, [(dep, type)])
    """

    unmet = []

    # If no dependencies, ok
    try:
        deps = manifest.dependencies
    except AttributeError:
        return True, unmet

    # Python dependencies
    pylibs = True
    if deps.pylibs:
        for dep in COMMA_SEP_LIST_PATTERN.split(deps.pylibs):
            if not is_python_lib_available(dep):
                unmet.append((dep, 'pylib'))
                pylibs = False

    # FreeCAD dependencies
    workbenches = True
    if deps.workbenches:
        for dep in COMMA_SEP_LIST_PATTERN.split(deps.workbenches):
            if not is_workbench_available(dep):
                unmet.append((dep, 'workbench'))
                workbenches = False

    # External dependencies
    external = True
    if deps.external:
        for dep in COMMA_SEP_LIST_PATTERN.split(deps.external):
            if not is_executable_available(dep):
                unmet.append((dep, 'external'))
                external = False

    return pylibs and workbenches and external, unmet
