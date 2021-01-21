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

from freecad.extman.sources.source_installed import InstalledPackageSource
import FreeCADGui as Gui
from pathlib import Path
import json
from random import randint
import hashlib

from freecad.extman import utils, log_err, tr
from freecad.extman.utils.preferences import ExtManParameters
from freecad.extman.gui.router import Router, route
from freecad.extman.sources.source_cloud import findSource, clearSourcesCache
from freecad.extman.utils.worker import Worker


# +---------------------------------------------------------------------------+
# | Request-Response based actions                                            |
# +---------------------------------------------------------------------------+


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


def show_uninstall_info(path, session, params, request, response):
    """
    Show information before uninstall
    """

    pkg_name = params['pkg']
    session.set_state(installResult=None)

    def job():
        pkg_source = InstalledPackageSource()
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


def uninstall_package(path, session, params, request, response):
    """
    Uninstall package
    """

    pkg_name = params['pkg']
    session.set_state(installResult=None)

    def job():
        pkg_source = InstalledPackageSource()
        install_pkg = pkg_source.findPackageByName(pkg_name)
        result = pkg_source.uninstall(install_pkg)
        session.set_state(pkgSource=pkg_source, pkgName=pkg_name, installPkg=install_pkg, installResult=result)
        session.route_to('/InstalledPackages')
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

    session.set_state(pkgSource=InstalledPackageSource())
    session.route_to('/InstalledPackages')
    response.render_template('index.html')


def set_package_viewmode(path, session, params, request, response):
    ExtManParameters.PackagesViewMode = params['vm']
    response.render_template('index.html')


def open_macro(path, session, params, request, response):
    """
    Open Macro in code editor
    """

    macro = Path(params['macro'])
    if macro.exists():
        Gui.open(str(macro.as_posix()))
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

    path = Path(params['macro'])
    try:
        Gui.doCommandGui("exec(open(\"{0}\").read())".format(path.as_posix()))
    except Exception as ex:
        log_err(tr("Error in macro:"), path, str(ex))

    response.html_ok()


# +---------------------------------------------------------------------------+
# | Javascript message based actions                                          |
# +---------------------------------------------------------------------------+


def on_form_add_source(data, session):

    result = {
        'status': 'ok',
        'validation': [],
        'message': None
    }

    if not data.get('title'):
        result['status'] = 'error'
        result['validation'].append({'field': 'title', 'message': tr('title is required')})

    if not data.get('url'):
        result['status'] = 'error'
        result['validation'].append({'field': 'url', 'message': tr('url is required')})

    if not data.get('protocol'):
        result['status'] = 'error'
        result['validation'].append({'field': 'protocol', 'message': tr('protocol is required')})

    if result['status'] != 'ok':
        result['message'] = tr('Validation error')
        return result

    name = str(hashlib.sha256(data['url'].encode()).hexdigest())
    sources = json.loads(ExtManParameters.CustomCloudSources)
    sources = [s for s in sources if s['name'] != name]

    if data.get('protocol') in ('github', 'framagit'):
        if not data['url'].endswith('.git'):
            data['url'] = data['url'].strip('/') + '.git'

    source = {
        'name': name,
        'title': data['title'],
        'description': data['description'],
        'git': data['url'],
        'protocol': data.get('protocol', 'github'),
        'type': 'Mod',
        'icon': 'html/img/package_source.svg'
    }
    sources.append(source)
    ExtManParameters.CustomCloudSources = json.dumps(sources)
    clearSourcesCache()
    return {"status": 'ok'}


def on_form_remove_source(data, session):
    name = str(hashlib.sha256(data['url'].encode()).hexdigest())
    sources = json.loads(ExtManParameters.CustomCloudSources)
    sources = [s for s in sources if s['name'] != name]
    ExtManParameters.CustomCloudSources = json.dumps(sources)
    clearSourcesCache()
    return {"status": 'ok'}


# +---------------------------------------------------------------------------+
# | Configuration                                                             |
# +---------------------------------------------------------------------------+


def create_router():
    """
    Setup routes
    """

    return Router(
        InstalledPackages=route(any_of=['/InstalledPackages', '/']),
        CloudSources=route(prefix="/CloudSources"),
        CloudSourcesPackages=route(prefix="/CloudSources/Packages"),
        Install=route(exact='/CloudSources/Packages/Install'),
        Uninstall=route(exact='/CloudSources/Packages/Install')
    )


# Functions exposed as actions to WebView
actions = {
    f.__name__: f
    for f in (
        restart,
        show_install_info,
        show_uninstall_info,
        install_package,
        uninstall_package,
        update_cloud_source,
        open_cloud_source,
        open_cloud,
        open_installed,
        set_package_viewmode,
        open_macro,
        open_workbench,
        run_macro
    )
}

# Message handlers
message_handlers = {
    f.__name__: f
    for f in (
        on_form_add_source,
        on_form_remove_source
    )
}
