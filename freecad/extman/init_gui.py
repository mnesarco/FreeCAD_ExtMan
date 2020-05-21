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
from FreeCAD import Console, GuiUp
from freecad.extman import ADDON_DIR

#***************************************************************************
#* ExtManWorkbench class                                                   *
#***************************************************************************
class ExtManWorkbench( Gui.Workbench ):

    def __init__(self):
        self.__class__.Icon = os.path.join(ADDON_DIR, 'Resources', 'icons', 'ExtManWorkbench.svg')
        self.__class__.MenuText = "Extension Manager"
        self.__class__.ToolTip = "Extension Manager"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        pass
    
    def Activated(self):
        from freecad.extman.browser import installRouter, startBrowser
        from freecad.extman.controller import createRouter
        installRouter(createRouter())
        startBrowser()

    def Deactivated(self):
        pass

#***************************************************************************
#* Add workbench to FreeCAD                                                *
#***************************************************************************
Gui.addWorkbench( ExtManWorkbench )

#------------------------------------------------------------------------------
# Setup GUI
if GuiUp:

    #! Important: 
    #!   Call this as soon as possible
    #!   before any WebEngineView is created in FreeCAD
    from .webview import registerCustomSchemes
    registerCustomSchemes()

