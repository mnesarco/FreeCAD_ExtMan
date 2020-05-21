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

#------------------------------------------------------------------------------
def restart(path, session, params, request, response):
    from freecad.extman import utils
    utils.restartFreeCAD()

#------------------------------------------------------------------------------
def show_install_info(path, session, params, request, response):

    """
    Show information before install
    """
    from freecad.extman.source_cloud import findSource
    
    channelId = params['channel']
    source = params['source']
    pkgName = params['pkg']
    session.setState(installResult=None)

    def job():
        pkgSource = findSource(channelId, source)
        if pkgSource:
            installPkg = pkgSource.findPackageByName(pkgName)
            if installPkg:
                session.setState(pkgSource=pkgSource, pkgName=pkgName, installPkg=installPkg)
                session.routeTo('/CloudSources/Packages/Install')
        response.renderTemplate('index.html')

    from freecad.extman.worker import Worker
    Worker(job).start()


#------------------------------------------------------------------------------
def install_package(path, session, params, request, response):

    """
    Install/Update package
    """
    from freecad.extman.source_cloud import findSource
    
    channelId = params['channel']
    source = params['source']
    pkgName = params['pkg']
    session.setState(installResult=None)

    def job():
        pkgSource = findSource(channelId, source)
        if pkgSource:
            installPkg = pkgSource.findPackageByName(pkgName)
            result = pkgSource.install(pkgName)
            session.setState(pkgSource=pkgSource, pkgName=pkgName, installPkg=installPkg, installResult=result)
            session.routeTo('/CloudSources/Packages/Install')
        response.renderTemplate('index.html')

    from freecad.extman.worker import Worker
    Worker(job).start()


#------------------------------------------------------------------------------
def update_cloud_source(path, session, params, request, response):

    """
    Update package list of the package source
    """

    from freecad.extman.source_cloud import findSource
    pkgSource = findSource(params['channel'], params['name'])
    if pkgSource:
        pkgSource.updatePackageList()
    
    open_cloud_source(path, session, params, request, response)

#------------------------------------------------------------------------------
def open_cloud_source(path, session, params, request, response):

    """
    List Packages from channel/source
    """

    def job():
        from freecad.extman.source_cloud import findSource
        pkgSource = findSource(params['channel'], params['name'])
        session.setState(pkgSource=pkgSource)
        session.routeTo('/CloudSources/Packages')
        response.renderTemplate('index.html')

    from freecad.extman.worker import Worker
    Worker(job).start()

#------------------------------------------------------------------------------
def open_cloud(path, session, params, request, response):

    """
    List Cloud channels
    """

    session.routeTo('/CloudSources')
    response.renderTemplate('index.html')

#------------------------------------------------------------------------------
def open_installed(path, session, params, request, response):

    """
    List installed packages
    """

    session.routeTo('/InstalledPackages')
    response.renderTemplate('index.html')

#------------------------------------------------------------------------------
def set_package_viewmode(path, session, params, request, response):
    from freecad.extman.preferences import ExtManParameters
    ExtManParameters.packagesViewMode = params['vm']
    response.renderTemplate('index.html')

#------------------------------------------------------------------------------
def open_macro(path, session, params, request, response):

    """
    Open Macro in code editor
    """

    import os
    macro = params['macro']
    print(macro)
    if os.path.exists(macro):
        fcpath = macro.replace('\\', '/')
        import FreeCADGui as Gui
        Gui.open(fcpath)
    response.htmlOk()

#------------------------------------------------------------------------------
def open_workbench(path, session, params, request, response):

    """
    Activate Workbench
    """

    import FreeCADGui as Gui
    Gui.activateWorkbench(params['workbenchKey'])    
    response.htmlOk()

#------------------------------------------------------------------------------
def run_macro(path, session, params, request, response):

    """
    Execute macro
    """

    import os
    path = params['macro']
    if os.path.exists(path):
        import FreeCADGui as Gui
        Gui.doCommandGui(f"exec(open(\"{path}\").read())")  
    response.htmlOk()
            
#------------------------------------------------------------------------------
def createRouter():

    """
    Setup routes
    """

    from freecad.extman.router import Router, Route
    return Router(
        InstalledPackages     = Route(anyOf=['/InstalledPackages', '/']),
        CloudSources          = Route(prefix="/CloudSources"),
        CloudSourcesPackages  = Route(prefix="/CloudSources/Packages"),
        Install               = Route(exact='/CloudSources/Packages/Install')
    )