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
# noinspection PyPep8Naming

import FreeCADGui as Gui
from FreeCAD import Console, GuiUp

from freecad.extman import get_resource_path, tr
from freecad.extman.browser import install_router, start_browser
from freecad.extman.controller import create_router
from freecad.extman.webview import register_custom_schemes


class ExtManWorkbench(Gui.Workbench):
    """Extension Manager Workbench"""

    Icon = get_resource_path('icons', 'ExtManWorkbench.svg')
    MenuText = tr("Extension Manager")
    ToolTip = tr("Extension Manager")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        pass

    def Activated(self):
        install_router(create_router())
        start_browser()

    def Deactivated(self):
        pass


# Load Workbench into FreeCAD
Gui.addWorkbench(ExtManWorkbench)

# Setup WebView GUI
if GuiUp:

    # ! Important:
    # !   Call this as soon as possible
    # !   before any WebEngineView is created in FreeCAD
    register_custom_schemes()
