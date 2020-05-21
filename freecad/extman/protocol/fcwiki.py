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

import re, json, os, traceback, sys

import FreeCAD as App

from freecad.extman import tr, getResourcePath
from freecad.extman.protocol import Protocol
from freecad.extman.protocol.http import httpGet
from freecad.extman.sources import PackageInfo, InstallResult
import freecad.extman.utils as utils
import freecad.extman.flags as flags
from urllib.parse import quote

# mediawiki Mod table row
# Very permisive because mediawiki is very permissive
MODTABLEITEM = re.compile(r"""
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
MACROLINK = re.compile(r"""
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
MACROCODE = re.compile(r"""
    \{\{MacroCode\s*\|\s*(code=)?
    (?P<code>.*?)
    \n\s*\}\}
    """, re.X | re.S)

def getPageContentFormJson(jsonObj):
    try:
        return jsonObj['query']['pages'][0]['revisions'][0]['slots']['main']['content']
    except:
        return None

class FCWikiProtocol(Protocol):

    def __init__(self, url, wiki):
        super().__init__()
        self.url = url
        self.wiki = wiki

    def getModList(self):
        return []

    def getMacroList(self):

        macros = []
        installDir = App.getUserMacroDir(True)
        defaultIcon = utils.pathToUrl(getResourcePath('html', 'img', 'package_macro.svg'))

        try:
            content = httpGet(self.url, timeout=45)
            if content:
                data = json.loads(content)
                wiki = getPageContentFormJson(data)

                for mlink in MACROLINK.finditer(wiki):

                    name = mlink.group('name').replace(' ', '_')
                    label = mlink.group('label')
                    description = mlink.group('description')

                    icon = mlink.group('icon')
                    if icon:
                        icon = self.wiki + '/Special:Redirect/file/' + icon.replace(' ', '_')
                    else:
                        icon = defaultIcon

                    pkg = PackageInfo(
                        key = name,
                        installDir = installDir,
                        installFile = os.path.join(installDir, name + '.FCMacro'),
                        name = name,
                        title = label,
                        description = description,
                        icon = icon,
                        isCore = False,
                        type = 'Macro',
                        isGit = False,
                        isWiki = True,
                        markedAsSafe = False,
                        categories = [tr('Uncategorized')],
                        date = None,
                        version = None,
                        readmeUrl = '{0}/Macro_{1}?origin=*'.format(self.wiki, name),
                        readmeFormat = 'html'              
                    )
                    flags.applyPredefinedFlags(pkg)
                    macros.append(pkg)

        except:
            traceback.print_exc(file=sys.stderr)
    
        return macros

    def getWikiPageUrlJson(self, name):
        return '{0}/api.php?action=query&prop=revisions&titles={1}&rvslots=%2A&rvprop=content&formatversion=2&format=json'.format(self.wiki, name)

    def installMacro(self, pkg):

        result = InstallResult()
        url = self.getWikiPageUrlJson("Macro_{0}".format(quote(pkg.name)))
        content = httpGet(url)
        if content:
            wikitext = getPageContentFormJson(json.loads(content))
            m = MACROCODE.search(wikitext)
            if m:
                with open(pkg.installFile, 'w', encoding='utf-8') as f:
                    f.write(m.group('code'))
                    result.ok = True
        
        return result

def getModIndex(url, wiki):
    index = {}
    content = httpGet(url)
    if content:
        data = getPageContentFormJson(json.loads(content))
        for row in MODTABLEITEM.finditer(data):
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
