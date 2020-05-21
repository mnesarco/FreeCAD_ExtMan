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
import random
import json
from freecad.extman.html_utils import getResourceUrl, Components
from freecad.extman import tr
from functools import lru_cache
import hashlib
from urllib.parse import quote

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

def PackageIcon(pkg, cssClass="icon", style=""):
    
    icon = pkg.getIcon()
    fallback = None
    if hasattr(pkg, 'iconSources'):
        sources = pkg.iconSources + ['img/package_greyed.svg']
        fallback = "||".join( (s for s in sources if s != icon ) )

    if fallback:
        fallback = fallback.replace("'", "")
        fallback = " data-fallback='{0}' ".format(fallback)
        onerror = " onerror='extman_onImageError(this)' "
    else:
        fallback = ''
        onerror = ''

    return '<img src="{0}" {1} class="{2}" style="{3}" {4} />'\
        .format(icon, fallback, cssClass, style, onerror)

@lru_cache()
def IconComponent(name, fallback='img/freecad.svg', title="", cssClass="icon"):
    url, ctx, absPath = getResourceUrl('img', name)
    if os.path.exists(absPath):
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

@lru_cache()
def BtnOpenMacro(pkg):
    if pkg.type == 'Macro' and pkg.isInstalled(): 
        macro = pkg.key.replace('"', r'\"')
        return """
        <a class="btn btn-sm btn-outline-success btn-labeled extman-ajax" 
            href="action.open_macro?macro={0}">
            {1}
        </a>
        """.format(macro, TR_EDIT)
    else:
        return ''

@lru_cache()
def BtnRunMacro(pkg):
    if pkg.type == 'Macro' and pkg.isInstalled(): 
        macro = pkg.installFile.replace('"', r'\"')
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

def BtnInstallPkg(pkg, source):
    if not pkg.isInstalled():
        return """
        <a class="btn btn-sm btn-outline-danger btn-labeled extman-loading" 
            href="action.show_install_info?pkg={0}&source={1}&channel={2}">
            {3}
        </a>
        """.format(quote(pkg.name), quote(source.name), quote(source.channelId), TR_INSTALL)
    else:
        return ''

def BtnDoInstallOrUpdatePkg(pkg):
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

def BtnUpdatePackage(pkg, source):
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

def BtnActivateWB(pkg):
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

@lru_cache()
def PkgAllBadges(pkg, showInstalled=True, showCore=True, withText=False, layout=None):
    badges = [
        PkgCoreBadge(pkg, withText=withText) if showCore else "",
        PkgTypeBadge(pkg, withText=withText),
        PkgInstalledBadge(pkg, withText=withText) if showInstalled else '',
        PkgGitBadge(pkg, withText=withText),
        PkgWikiBadge(pkg, withText=withText)
    ]
    if layout == 'list':
        return "".join((
            '<li class="list-group-item pkg-badge-list-item">{0}</li>'.format(b)
            for b in badges if b != ''
        ))
    else:
        return "".join(badges)



@lru_cache()
def PkgCoreBadge(pkg, withText=False):

    if pkg.isCore:
        icon = IconComponent('package_core.svg', title=TR_CORE_PACKAGE, cssClass='icon-sm')
        text = TR_CORE_PACKAGE
    else:
        icon = IconComponent('package_community.svg', title=TR_COMMUNITY_PACKAGE, cssClass='icon-sm')
        text = TR_COMMUNITY_PACKAGE
    
    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon

@lru_cache()
def PkgTypeBadge(pkg, withText=False):
    if pkg.type == 'Workbench':
        text = TR_WORKBENCH
        icon = IconComponent('package_workbench.svg', title=text, cssClass='icon-sm')
    elif pkg.type == 'Macro':
        text = TR_MACRO
        icon = IconComponent('package_macro_badge.svg', title=text, cssClass='icon-sm')        
    elif pkg.type == 'Mod':
        text = TR_MODULE
        icon = IconComponent('package_mod.svg', title=text, cssClass='icon-sm')
    else:
        return ''

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon


@lru_cache()
def PkgInstalledBadge(pkg, withText=False):
    if pkg.isInstalled():
        text = TR_INSTALLED
        icon = IconComponent('package_installed.svg', title=text, cssClass='icon-sm')
    else:
        return ''

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon

@lru_cache()
def PkgGitBadge(pkg, withText=False):
    if pkg.isGit:
        text = TR_GIT
        icon = IconComponent('git.svg', title=text, cssClass='icon-sm')
    else:
        return ''

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon

@lru_cache()
def PkgWikiBadge(pkg, withText=False):
    if pkg.isWiki:
        text = TR_WIKI
        icon = IconComponent('wiki.svg', title=text, cssClass='icon-sm')
    else:
        return ''

    if withText:
        return "{0} <span>{1}</span>".format(icon, text)
    else:
        return icon

def PackageViewModeSelect(mode):
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

@lru_cache()
def PkgFlags(pkg, withText=False, layout=None):
    icons = []
    if hasattr(pkg, 'flags'):
        flags = pkg.flags
        if 'obsolete' in flags:
            text = TR_FLAG_OBSOLETE
            icon = IconComponent('flag_obsolete.svg', title=text, cssClass='icon-sm')
            icons.append((text, icon))
        if 'py2only' in flags:
            text = TR_FLAG_PY2ONLY
            icon = IconComponent('flag_py2only.svg', title=TR_FLAG_PY2ONLY, cssClass='icon-sm')
            icons.append((text, icon))
    
    if withText:
        out = ('{0} <span>{1}</span>'.format(icon, text) for (text, icon) in icons)
    else:
        out = (icon for (text,icon) in icons)
    
    if layout == 'list':
        return "".join((
            '<li class="list-group-item pkg-flag-list-item">{0}</li>'.format(b)
            for b in out if b != ''
        ))
    else:
        return "".join(out)

@lru_cache()
def PkgReadmeLink(pkg, cssClass=""):
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
    icon = IconComponent,
    BtnOpenMacro = BtnOpenMacro,
    BtnRunMacro = BtnRunMacro,
    BtnActivateWB = BtnActivateWB,
    BtnUpdatePackage = BtnUpdatePackage,
    BtnInstallPackage = BtnInstallPkg,
    PkgCoreBadge = PkgCoreBadge,
    PkgTypeBadge = PkgTypeBadge,
    PkgInstalledBadge = PkgInstalledBadge,
    PkgGitBadge = PkgGitBadge,
    PkgWikiBadge = PkgWikiBadge,
    PackageViewModeSelect = PackageViewModeSelect,
    PackageIcon = PackageIcon,
    PkgAllBadges = PkgAllBadges,
    PkgFlags = PkgFlags,
    PkgReadmeLink = PkgReadmeLink,
    BtnDoInstallOrUpdatePkg = BtnDoInstallOrUpdatePkg
)