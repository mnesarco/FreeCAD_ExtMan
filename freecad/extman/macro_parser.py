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

import FreeCAD as App
import os
import re

import freecad.extman.utils as utils
from freecad.extman import get_resource_path, tr
from freecad.extman.sources import PackageInfo

# Regex for tags __tag__ = value
MACRO_TAG_PATTERN = re.compile(r'''
    ^\s*
    __(?P<tag>\w+?)__
    \s*=\s*
    (
        ( (?P<sq>\'|\'{3}) (?P<svalue>[^\']+?) (?P=sq) )
        |
        ( (?P<dq>"|"{3})   (?P<dvalue>[^"]+?) (?P=dq) )
    )
    ''',
                               re.I | re.S | re.M | re.X)

# Allowed tags (Constant)
MACRO_TAG_FILTER = [
    'name', 'title', 'author', 'version', 'date', 'comment',
    'web', 'wiki', 'icon', 'license', 'iconw', 'help', 'status',
    'requires', 'communication', 'categories', 'download', 'files',
    'description', 'readme'
]

# Regex to split comma separated string list
COMMA_SEP_LIST_PATTERN = re.compile(r'\s*,\s*', re.S)


def get_macro_tags(code, path):
    tags = {k: None for k in MACRO_TAG_FILTER}
    for m in MACRO_TAG_PATTERN.finditer(code):
        tag = m.group('tag').lower()
        if tag in MACRO_TAG_FILTER:
            val = m.group('svalue') or m.group('dvalue')
            tags[tag] = utils.SanitizedHtml(val)
    return tags


def build_macro_package(path, pfile, is_core=False, is_git=False, is_wiki=False, install_path=None, base_path=""):
    with open(path, 'r', encoding='utf-8') as f:
        tags = get_macro_tags(f.read(), path)
        install_dir = App.getUserMacroDir(True)
        base = dict(
            key=install_path or path,
            type='Macro',
            isCore=is_core,
            installDir=install_dir,
            installFile=os.path.join(install_dir, os.path.basename(path)),
            isGit=is_git,
            isWiki=is_wiki,
            basePath=base_path
        )
        tags.update(base)

        if not tags['title']:
            tags['title'] = tags['name'] or pfile

        tags['name'] = pfile  # Always override name with actual file name

        if not tags['icon']:
            tags['icon'] = get_resource_path('html', 'img', 'package_macro.svg')

        if not os.path.exists(tags['icon']):
            tags['icon'] = get_resource_path('html', 'img', 'package_macro.svg')

        tags['icon'] = utils.path_to_url(tags['icon'])

        if tags['comment']:
            tags['description'] = tags['comment']

        if not tags['description']:
            tags['description'] = tr('Warning! No description')

        if tags['categories']:
            cats = COMMA_SEP_LIST_PATTERN.split(tags['categories'])
            tags['categories'] = [tr(c) for c in cats]
        else:
            tags['categories'] = [tr('Uncategorized')]

        if tags['files']:
            tags['files'] = COMMA_SEP_LIST_PATTERN.split(tags['files'])

        if tags['readme']:
            tags['readmeUrl'] = tags['readme']
            tags['readmeFormat'] = 'html'
        elif tags['wiki']:
            tags['readmeUrl'] = tags['wiki']
            tags['readmeFormat'] = 'html'
        elif tags['web']:
            tags['readmeUrl'] = tags['web']
            tags['readmeFormat'] = 'html'

        return PackageInfo(**tags)
