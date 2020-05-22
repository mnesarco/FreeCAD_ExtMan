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

from freecad.extman import utils
from freecad.extman.preferences import ExtManParameters
from freecad.extman.router import Router, route
from freecad.extman.source_cloud import findSource
from freecad.extman.worker import Worker


def restart(path, session, params, request, response):
    utils.restart_freecad()


def show_install_info(path, session, params, request, response):
    """
    Show information before install
    """

    channel_id = params['channel']
    source = params['source']
    pkg_name = params['pkg']
    session.set_state(installResult=None)

    def job():
        pkg_source = findSource(channel_id, source)
        if pkg_source:
            install_pkg = pkg_source.findPackageByName(pkg_name)
            if install_pkg:
                session.set_state(pkgSource=pkg_source, pkgName=pkg_name, installPkg=install_pkg)
                session.route_to('/CloudSources/Packages/Install')
        response.render_template('index.html')

    Worker(job).start()


def install_package(path, session, params, request, response):
    """
    Install/Update package
    """

    channel_id = params['channel']
    source = params['source']
    pkg_name = params['pkg']
    session.set_state(installResult=None)

    def job():
        pkg_source = findSource(channel_id, source)
        if pkg_source:
            install_pkg = pkg_source.findPackageByName(pkg_name)
            result = pkg_source.install(pkg_name)
            session.set_state(pkgSource=pkg_source, pkgName=pkg_name, installPkg=install_pkg, installResult=result)
            session.route_to('/CloudSources/Packages/Install')
        response.render_template('index.html')

    Worker(job).start()


def update_cloud_source(path, session, params, request, response):
    """
    Update package list of the package source
    """

    pkg_source = findSource(params['channel'], params['name'])
    if pkg_source:
        pkg_source.updatePackageList()

    open_cloud_source(path, session, params, request, response)


def open_cloud_source(path, session, params, request, response):
    """
    List Packages from channel/source
    """

    def job():
        pkg_source = findSource(params['channel'], params['name'])
        session.set_state(pkgSource=pkg_source)
        session.route_to('/CloudSources/Packages')
        response.render_template('index.html')

    Worker(job).start()


def open_cloud(path, session, params, request, response):
    """
    List Cloud channels
    """

    session.route_to('/CloudSources')
    response.render_template('index.html')


def open_installed(path, session, params, request, response):
    """
    List installed packages
    """

    session.route_to('/InstalledPackages')
    response.render_template('index.html')


def set_package_viewmode(path, session, params, request, response):
    ExtManParameters.packagesViewMode = params['vm']
    response.render_template('index.html')


def open_macro(path, session, params, request, response):
    """
    Open Macro in code editor
    """

    macro = params['macro']
    if os.path.exists(macro):
        Gui.open(macro.replace('\\', '/'))
    response.html_ok()


def open_workbench(path, session, params, request, response):
    """
    Activate Workbench
    """

    Gui.activateWorkbench(params['workbenchKey'])
    response.html_ok()


def run_macro(path, session, params, request, response):
    """
    Execute macro
    """

    path = params['macro']
    if os.path.exists(path):
        Gui.doCommandGui("exec(open(\"{0}\").read())".format(path))
    response.html_ok()


def create_router():
    """
    Setup routes
    """

    return Router(
        InstalledPackages=route(any_of=['/InstalledPackages', '/']),
        CloudSources=route(prefix="/CloudSources"),
        CloudSourcesPackages=route(prefix="/CloudSources/Packages"),
        Install=route(exact='/CloudSources/Packages/Install')
    )
