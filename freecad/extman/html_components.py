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


import hashlib
import json
import os
import random
from functools import lru_cache
from urllib.parse import quote

from freecad.extman import tr
from freecad.extman.html_utils import get_resource_url, Components

TR_RUN = tr('Run')
TR_CLOSE = tr('Close')
TR_EDIT = tr('Edit')
TR_ACTIVATE = tr('Activate')
TR_UPDATE = tr('Update')
TR_CORE_PACKAGE = tr('Core Package')
TR_COMMUNITY_PACKAGE = tr('Community Package')
TR_WORKBENCH = tr('Workbench')
TR_MACRO = tr('Macro')
TR_MODULE = tr('Module')
TR_INSTALLED = tr('Installed')
TR_GIT = tr('Git')
TR_WIKI = tr('Wiki')
TR_FLAG_OBSOLETE = tr('Obsolete package')
TR_FLAG_PY2ONLY = tr('Python2 only')
TR_README = tr('readme')
TR_INSTALL = tr('Install')
TR_INSTALLING = tr('Installing...')
TR_VIEWMODE = tr('View mode')
TR_VIEWMODE_LIST = tr('List view')
TR_VIEWMODE_CARD = tr('Card view')


def comp_package_icon(pkg, cssClass="icon", style=""):

    icon = pkg.getIcon()
    fallback = None

    if hasattr(pkg, 'iconSources'):
        sources = pkg.iconSources + ['img/package_greyed.svg']
        fallback = "||".join((s for s in sources if s != icon))

    if fallback:
        fallback = fallback.replace("'", "")
        fallback = " data-fallback='{0}' ".format(fallback)
        onerror = " onerror='extman_onImageError(this)' "
    else:
        fallback = ''
        onerror = ''

    return '<img src="{0}" {1} class="{2}" style="{3}" {4} />' \
        .format(icon, fallback, cssClass, style, onerror)


def comp_icon(name, fallback='img/freecad.svg', title="", cssClass="icon"):
    url, ctx, abs_path = get_resource_url('img', name)
    if os.path.exists(abs_path):
        return """
        <img 
            src="{0}" 
            data-fallback="{1}"
            alt="{2}" 
            title="{2}" 
            class="{3}" />
        """.format(url, fallback, title, cssClass)
    else:
        return "???{0}???".format(name)


def comp_btn_open_macro(pkg):
    if pkg.type == 'Macro' and pkg.isInstalled():
        macro = pkg.installFile.replace('\\', '/')
        macro = macro.replace('"', r'\"')
        return """
        <a class="btn btn-sm btn-outline-success btn-labeled extman-ajax" 
            href="action.open_macro?macro={0}">
            {1}
        </a>
        """.format(macro, TR_EDIT)
    else:
        return ''


def comp_btn_run_macro(pkg):
    if pkg.type == 'Macro' and pkg.isInstalled():
        macro = pkg.installFile.replace('\\', '/')
        macro = macro.replace('"', r'\"')
        if pkg.markedAsSafe:
            return """
            <button class="btn btn-sm btn-outline-danger btn-labeled" 
                onclick="extman_runMacro('{0}')">
                {1}
            </button>
            """.format(macro, TR_RUN)
        else:
            title = pkg.title.replace('"', r'\"')
            return """
            <button class="btn btn-sm btn-outline-danger btn-labeled" 
                onclick='extman_confirmMacro("{0}", "{1}")'>
                {2}
            </button>
            """.format(macro, title, TR_RUN)
    else:
        return ''


def comp_btn_install_package(pkg, source):
    if not pkg.isInstalled():
        return """
        <a class="btn btn-sm btn-outline-danger btn-labeled extman-loading" 
            href="action.show_install_info?pkg={0}&source={1}&channel={2}">
            {3}
        </a>
        """.format(quote(pkg.name), quote(source.name), quote(source.channelId), TR_INSTALL)
    else:
        return ''


def comp_btn_install_or_update_package(pkg):
    return """
    <a class="btn btn-danger extman-loading" data-spinner-message="{0}"
        href="action.install_package?pkg={1}&source={2}&channel={3}">
        {4}
    </a>
    """.format(
        TR_INSTALLING,
        quote(pkg.name),
        quote(pkg.sourceName),
        quote(pkg.channelId),
        TR_UPDATE if pkg.isInstalled() else TR_INSTALL)


def comp_btn_update_package(pkg, source):
    if pkg.isInstalled() and (not pkg.isCore) and pkg.channelId and pkg.sourceName:
        return """
        <a class="btn btn-sm btn-outline-primary btn-labeled extman-loading" 
            href="action.show_install_info?pkg={0}&source={1}&channel={2}">
            {3}
        </a>
        """.format(
            quote(pkg.name),
            quote(pkg.sourceName),
            quote(pkg.channelId),
            TR_UPDATE)
    else:
        return ''


def comp_btn_activate_wb(pkg):
    if pkg.type == 'Workbench' and pkg.isInstalled():
        key = pkg.key.replace('"', r'\"')
        return """
        <a class="btn btn-sm btn-outline-primary btn-labeled extman-ajax" 
            href="action.open_workbench?workbenchKey={0}">
            {1}
        </a>
        """.format(quote(key), TR_ACTIVATE)
    else:
        return ''


def comp_package_badges(pkg, showInstalled=True, showCore=True, withText=False, layout=None):
    badges = [
        comp_badge_core(pkg, withText=withText) if showCore else "",
        comp_badge_type(pkg, withText=withText),
        comp_badge_installed(pkg, withText=withText) if showInstalled else '',
        comp_badge_git(pkg, withText=withText),
        comp_badge_wiki(pkg, withText=withText)
    ]
    if layout == 'list':
        return "".join((
            '<li class="list-group-item pkg-badge-list-item">{0}</li>'.format(b)
            for b in badges if b != ''
        ))
    else:
        return "".join(badges)


def comp_badge_core(pkg, withText=False):
    if pkg.isCore:
        icon = comp_icon('package_core.svg', title=TR_CORE_PACKAGE, cssClass='icon-sm')
        text = TR_CORE_PACKAGE
    else:
        icon = comp_icon('package_community.svg', title=TR_COMMUNITY_PACKAGE, cssClass='icon-sm')
        text = TR_COMMUNITY_PACKAGE

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon


def comp_badge_type(pkg, withText=False):
    if pkg.type == 'Workbench':
        text = TR_WORKBENCH
        icon = comp_icon('package_workbench.svg', title=text, cssClass='icon-sm')
    elif pkg.type == 'Macro':
        text = TR_MACRO
        icon = comp_icon('package_macro_badge.svg', title=text, cssClass='icon-sm')
    elif pkg.type == 'Mod':
        text = TR_MODULE
        icon = comp_icon('package_mod.svg', title=text, cssClass='icon-sm')
    else:
        return ''

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon


def comp_badge_installed(pkg, withText=False):
    if pkg.isInstalled():
        text = TR_INSTALLED
        icon = comp_icon('package_installed.svg', title=text, cssClass='icon-sm')
    else:
        return ''

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon


def comp_badge_git(pkg, withText=False):
    if pkg.isGit:
        text = TR_GIT
        icon = comp_icon('git.svg', title=text, cssClass='icon-sm')
    else:
        return ''

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon


def comp_badge_wiki(pkg, withText=False):
    if pkg.isWiki:
        text = TR_WIKI
        icon = comp_icon('wiki.svg', title=text, cssClass='icon-sm')
    else:
        return ''

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon


def comp_select_viewmode(mode):
    return """
        <div class="btn-group btn-group-sm float-right" role="group" aria-label="{0}" 
            style="margin-top: 10px; margin-right:10px; position: absolute; right: 20px;">
            <a href="action.set_package_viewmode?vm=rows" class="btn btn-sm btn-outline-secondary {1}" title="{2}">
                <img src="img/bootstrap/list.svg" />
            </a>
            <a href="action.set_package_viewmode?vm=cards" class="btn btn-sm btn-outline-secondary {3}" title="{4}">
                <img src="img/bootstrap/grid.svg" />
            </a>
        </div>
        """.format(
        TR_VIEWMODE,
        'active' if mode == 'rows' else '',
        TR_VIEWMODE_LIST,
        'active' if mode == 'cards' else '',
        TR_VIEWMODE_CARD)


def comp_package_flags(pkg, withText=False, layout=None):
    icons = []
    if hasattr(pkg, 'flags'):
        flags = pkg.flags
        if 'obsolete' in flags:
            text = TR_FLAG_OBSOLETE
            icon = comp_icon('flag_obsolete.svg', title=text, cssClass='icon-sm')
            icons.append((text, icon))
        if 'py2only' in flags:
            text = TR_FLAG_PY2ONLY
            icon = comp_icon('flag_py2only.svg', title=TR_FLAG_PY2ONLY, cssClass='icon-sm')
            icons.append((text, icon))

    if withText:
        out = ('{0} <span>{1}</span>'.format(icon, text) for (text, icon) in icons)
    else:
        out = (icon for (text, icon) in icons)

    if layout == 'list':
        return "".join((
            '<li class="list-group-item pkg-flag-list-item">{0}</li>'.format(b)
            for b in out if b != ''
        ))
    else:
        return "".join(out)


def comp_link_readme(pkg, cssClass=""):
    if pkg.readmeUrl:
        return """
        <a class="{0}" 
            href="#" 
            onclick="extman_readmeDlg(this, event)"
            data-readme="{1}"
            data-readmeformat="{2}"
            data-title="{3}">
            {4}
        </a>
        """.format(
            cssClass or 'readme-link',
            pkg.readmeUrl,
            pkg.readmeFormat,
            pkg.title,
            TR_README
        )
    else:
        return ''


# Components visible in all templates
components = Components(
    Icon=comp_icon,
    BtnOpenMacro=comp_btn_open_macro,
    BtnRunMacro=comp_btn_run_macro,
    BtnActivateWB=comp_btn_activate_wb,
    BtnUpdatePackage=comp_btn_update_package,
    BtnInstallPackage=comp_btn_install_package,
    PkgCoreBadge=comp_badge_core,
    PkgTypeBadge=comp_badge_type,
    PkgInstalledBadge=comp_badge_installed,
    PkgGitBadge=comp_badge_git,
    PkgWikiBadge=comp_badge_wiki,
    PackageViewModeSelect=comp_select_viewmode,
    PackageIcon=comp_package_icon,
    PkgAllBadges=comp_package_badges,
    PkgFlags=comp_package_flags,
    PkgReadmeLink=comp_link_readme,
    BtnDoInstallOrUpdatePkg=comp_btn_install_or_update_package
)
