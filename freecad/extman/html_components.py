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

def PackageIcon(pkg, cssClass="icon", style=""):
    
    icon = pkg.getIcon()
    fallback = None
    if hasattr(pkg, 'iconSources'):
        sources = pkg.iconSources + ['img/package_greyed.svg']
        fallback = "||".join( (s for s in sources if s != icon ) )

    if fallback:
        fallback = fallback.replace("'", "")
        fallback = f" data-fallback='{fallback}' "
        onerror = " onerror='extman_onImageError(this)' "
    else:
        fallback = ''
        onerror = ''

    return f"""
    <img src="{icon}" {fallback} class="{cssClass}" style="{style}" {onerror} />
    """

@lru_cache()
def IconComponent(name, fallback='img/freecad.svg', title="", cssClass="icon"):
    url, ctx, absPath = getResourceUrl('img', name)
    if os.path.exists(absPath):
        return f"""
        <img 
            src="{url}" 
            data-fallback="{fallback}"
            alt="{title}" 
            title="{title}" 
            class="{cssClass}" />
        """
    else:
        return f"???{name}???"

@lru_cache()
def BtnOpenMacro(pkg):
    if pkg.type == 'Macro' and pkg.isInstalled(): 
        macro = pkg.key.replace('"', r'\"')
        return f"""
        <a class="btn btn-sm btn-outline-success btn-labeled extman-ajax" 
            href="action.open_macro?macro={macro}">
            {TR_EDIT}
        </a>
        """
    else:
        return ''

@lru_cache()
def BtnRunMacro(pkg):
    if pkg.type == 'Macro' and pkg.isInstalled(): 
        macro = pkg.installFile.replace('"', r'\"')
        if pkg.markedAsSafe:
            return f"""
            <button class="btn btn-sm btn-outline-danger btn-labeled" 
                onclick="extman_runMacro('{macro}')">
                {TR_RUN}
            </button>
            """
        else:
            title = pkg.title.replace('"', r'\"')
            return f"""
            <button class="btn btn-sm btn-outline-danger btn-labeled" 
                onclick='extman_confirmMacro("{macro}", "{title}")'>
                {TR_RUN}
            </button>
            """
    else:
        return ''

def BtnInstallPkg(pkg, source):
    if not pkg.isInstalled():
        return f"""
        <a class="btn btn-sm btn-outline-danger btn-labeled extman-loading" 
            href="action.show_install_info?pkg={quote(pkg.name)}&source={quote(source.name)}&channel={quote(source.channelId)}">
            {TR_INSTALL}
        </a>
        """
    else:
        return ''

def BtnDoInstallOrUpdatePkg(pkg):
    return f"""
    <a class="btn btn-danger extman-loading" data-spinner-message="{TR_INSTALLING}"
        href="action.install_package?pkg={quote(pkg.name)}&source={quote(pkg.sourceName)}&channel={quote(pkg.channelId)}">
        {TR_UPDATE if pkg.isInstalled() else TR_INSTALL}
    </a>
    """

def BtnUpdatePackage(pkg, source):
    if pkg.isInstalled() and (not pkg.isCore) and pkg.channelId and pkg.sourceName:
        return f"""
        <a class="btn btn-sm btn-outline-primary btn-labeled extman-loading" 
            href="action.show_install_info?pkg={quote(pkg.name)}&source={quote(pkg.sourceName)}&channel={quote(pkg.channelId)}">
            {TR_UPDATE}
        </a>
        """
    else:
        return ''

def BtnActivateWB(pkg):
    if pkg.type == 'Workbench' and pkg.isInstalled():
        key = pkg.key.replace('"', r'\"')
        return f"""
        <a class="btn btn-sm btn-outline-primary btn-labeled extman-ajax" 
            href="action.open_workbench?workbenchKey={quote(key)}">
            {TR_ACTIVATE}
        </a>
        """
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
            f'<li class="list-group-item pkg-badge-list-item">{b}</li>'
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
        return f"{icon} <span>{text}</span>"
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
        return f"{icon} <span>{text}</span>"
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
        return f"{icon} <span>{text}</span>"
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
        return f"{icon} <span>{text}</span>"
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
        return f"{icon} <span>{text}</span>"
    else:
        return icon

def PackageViewModeSelect(mode):
    return f"""
    <div class="btn-group btn-group-sm float-right" role="group" aria-label="{tr('View Mode')}" 
        style="margin-top: 10px; margin-right:10px; position: absolute; right: 20px;">
        <a href="action.set_package_viewmode?vm=rows" class="btn btn-sm btn-outline-secondary {'active' if mode == 'rows' else ''}" title="{tr('List View')}">
            <img src="img/bootstrap/list.svg" />
        </a>
        <a href="action.set_package_viewmode?vm=cards" class="btn btn-sm btn-outline-secondary {'active' if mode == 'cards' else ''}" title="{tr('Card View')}">
            <img src="img/bootstrap/grid.svg" />
        </a>
    </div>
    """

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
        out = (f'{icon} <span>{text}</span>' for (text,icon) in icons)
    else:
        out = (f'{icon}' for (text,icon) in icons)
    
    if layout == 'list':
        return "".join((
            f'<li class="list-group-item pkg-flag-list-item">{b}</li>'
            for b in out if b != ''
        ))
    else:
        return "".join(out)

@lru_cache()
def PkgReadmeLink(pkg, cssClass=""):
    if pkg.readmeUrl:
        return f"""
        <a class="{cssClass or 'readme-link'}" 
            href="#" 
            onclick="extman_readmeDlg(this, event)"
            data-readme="{pkg.readmeUrl}"
            data-readmeformat="{pkg.readmeFormat}"
            data-title="{pkg.title}">
            {TR_README}
        </a>
        """
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