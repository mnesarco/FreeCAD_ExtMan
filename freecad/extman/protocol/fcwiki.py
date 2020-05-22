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

import FreeCAD as App
import json
import os
import re
import sys
import traceback
from urllib.parse import quote

import freecad.extman.flags as flags
import freecad.extman.utils as utils
from freecad.extman import tr, get_resource_path
from freecad.extman.protocol import Protocol
from freecad.extman.protocol.http import http_get
from freecad.extman.sources import PackageInfo, InstallResult

# mediawiki Mod table row
# Very permissive because mediawiki is very permissive
MOD_TABLE_ITEM = re.compile(r"""
        \n\|+-
        \s+\|+(\[\[(File|Image):(?P<icon>.*?)(\|.*?)\]\])?
        \s+\|+\[\[(?P<name>.*?)(\|(?P<title>.*?))?\]\]
        \s+\|+(?P<topics>.*)
        \s+\|+(?P<description>.*)
        (\n[^|].*)?
        \s+\|+(?P<authors>.*)
        \s+\|+(?P<code>.*)
        (\s+\|+(?!-)(?P<flag>.*))?
    """, re.X | re.I | re.M)

# Macro Metadata from mediawiki
# * {{MacroLink|Icon=<icon>|Macro <name>/<lang>|Macro <label>}}: <description>
MACRO_LINK = re.compile(r"""
    \{\{
        MacroLink                  \s*\|
        ((Icon=(?P<icon>[^|]+))       \|)?
        Macro[ _](?P<name>[^|/]+)
        (?P<lang>/[^|]+)?             \|
        (Macro[ _])?(?P<label>[^|]+) \s*
    \}\}
    \s*:\s*
    (?P<description>.*?)$
    """, re.X | re.I | re.M)

# Macro Code from mediawiki
MACRO_CODE = re.compile(r"""
    \{\{MacroCode\s*\|\s*(code=)?
    (?P<code>.*?)
    \n\s*\}\}
    """, re.X | re.S)


def get_page_content_from_json(jsonObj):
    try:
        return jsonObj['query']['pages'][0]['revisions'][0]['slots']['main']['content']
    except:
        return None


class FCWikiProtocol(Protocol):

    """
    Implements api calls to https://wiki.freecadweb.org (MediaWiki)
    """

    def __init__(self, url, wiki):
        super().__init__()
        self.url = url
        self.wiki = wiki

    def getModList(self):
        return []

    def getMacroList(self):

        macros = []
        install_dir = App.getUserMacroDir(True)
        default_icon = utils.path_to_url(get_resource_path('html', 'img', 'package_macro.svg'))

        try:
            content = http_get(self.url, timeout=45)
            if content:
                data = json.loads(content)
                wiki = get_page_content_from_json(data)

                for m_link in MACRO_LINK.finditer(wiki):

                    name = m_link.group('name').replace(' ', '_')
                    label = m_link.group('label')
                    description = m_link.group('description')

                    icon = m_link.group('icon')
                    if icon:
                        icon = self.wiki + '/Special:Redirect/file/' + icon.replace(' ', '_')
                    else:
                        icon = default_icon

                    pkg = PackageInfo(
                        key=name,
                        installDir=install_dir,
                        installFile=os.path.join(install_dir, name + '.FCMacro'),
                        name=name,
                        title=label,
                        description=description,
                        icon=icon,
                        isCore=False,
                        type='Macro',
                        isGit=False,
                        isWiki=True,
                        markedAsSafe=False,
                        categories=[tr('Uncategorized')],
                        date=None,
                        version=None,
                        readmeUrl='{0}/Macro_{1}?origin=*'.format(self.wiki, name),
                        readmeFormat='html'
                    )
                    flags.apply_predefined_flags(pkg)
                    macros.append(pkg)

        except:
            traceback.print_exc(file=sys.stderr)

        return macros

    def getWikiPageUrlJson(self, name):
        return '{0}/api.php?action=query&prop=revisions&titles={1}&rvslots=%2A&rvprop=content&formatversion=2&format=json'.format(
            self.wiki, name)

    def installMacro(self, pkg):

        result = InstallResult()
        url = self.getWikiPageUrlJson("Macro_{0}".format(quote(pkg.name)))
        content = http_get(url)
        if content:
            wikitext = get_page_content_from_json(json.loads(content))
            m = MACRO_CODE.search(wikitext)
            if m:
                with open(pkg.installFile, 'w', encoding='utf-8') as f:
                    f.write(m.group('code'))
                    result.ok = True

        return result


def get_mod_index(url, wiki):
    index = {}
    content = http_get(url)
    if content:
        data = get_page_content_from_json(json.loads(content))
        for row in MOD_TABLE_ITEM.finditer(data):
            repo = row.group('code')
            if repo.endswith('/'):
                repo = repo[:-1]
            item = {
                'name': row.group('name'),
                'title': row.group('title') or row.group('name'),
                'description': row.group('description'),
                'categories': row.group('topics'),
                'author': row.group('authors'),
                'repo': repo,
                'flag': row.group('flag')
            }
            icon = row.group('icon')
            if icon:
                item['icon'] = wiki + '/Special:Redirect/file/' + icon.replace(' ', '_')
            index[repo] = item
    return index
