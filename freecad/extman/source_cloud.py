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
import FreeCADGui as Gui
import json
import os
import re
import time

from freecad.extman import get_resource_path, tr
from freecad.extman import utils
from freecad.extman.protocol.fcwiki import FCWikiProtocol
from freecad.extman.protocol.github import GithubProtocol
from freecad.extman.sources import PackageInfo, PackageSource, PackageCategory, UnsupportedSourceException, \
    groupPackagesInCategories, savePackageMetadata


class CloudPackageSource(PackageSource):

    def __init__(self, data, channelId):
        super().__init__('Cloud:' + data['protocol'])

        self.channelId = channelId
        self.name = data['name']
        self.title = tr(data['title'])
        self.description = tr(data['description'])
        self.protocolName = data['protocol']
        self.cacheTime = 0
        self.type = data['type']

        icon = data['icon']
        if icon.startswith('html/img/'):
            self.icon = utils.path_to_url(get_resource_path(*icon.split('/')))
        else:
            self.icon = icon

        if data['protocol'] == 'github':
            self.protocol = GithubProtocol(
                data['git'],
                data.get('git_submodules'),
                data.get('index_type'),
                data.get('index_url'),
                data.get('wiki'),
            )

        elif data['protocol'] == 'fcwiki':
            self.protocol = FCWikiProtocol(data['url'], data['wiki'])

        else:
            raise UnsupportedSourceException("Unsupported protocol: {0}".format(data['protocol']))

        self.updates = {}

    def getTitle(self):
        return self.title

    def getDescription(self):
        return self.description

    def getIcon(self):
        return self.icon

    def getProtocolIcon(self):
        return utils.path_to_url(get_resource_path('html', 'img', 'source_cloud_{0}.svg'.format(self.protocolName)))

    def getPackages(self, cache=True):

        """IMPORTANT: 
            Does not support cache, to obtain cached
            results, use getCategories.
        """

        packages = []

        # Add Mods
        if self.type in ('Mod', 'Workbench'):
            packages.extend(self.protocol.getModList())

        # Add Macros
        if self.type == 'Macro':
            packages.extend(self.protocol.getMacroList())

        # Set source ownership
        for pkg in packages:
            pkg.sourceName = self.name
            pkg.channelId = self.channelId

        # Remove banned packages
        packages = list(filter(lambda pkg: 'banned' not in pkg.flags, packages))

        # Sort
        packages.sort(key=lambda p: p.title.lower())

        return packages

    def getCategories(self, cache=True):
        if not cache:
            categories = groupPackagesInCategories(self.getPackages(False))
            self.storeCacheData(categories)
        else:
            categories = self.loadCacheData()
            if not categories:
                categories = groupPackagesInCategories(self.getPackages(False))
                self.storeCacheData(categories)
        return categories

    def getCacheFile(self):
        store = get_resource_path('cache')
        if not os.path.exists(store):
            os.mkdir(store)
        filename = re.sub(r'\W+', '-', "{0}-{1}".format(self.channelId, self.name)) + '.json'
        store = get_resource_path('cache', filename)
        return store

    def updatePackageList(self):
        cacheFile = self.getCacheFile()
        if os.path.exists(cacheFile):
            os.remove(cacheFile)

    def storeCacheData(self, categories):
        filename = self.getCacheFile()
        jcats = []
        for cat in categories:
            jpkgs = []
            for pkg in cat.packages:
                jpkgs.append(pkg.__dict__)
            jcats.append({'name': cat.name, 'packages': jpkgs})
        with open(filename, 'w', encoding='utf-8') as f:
            content = json.dumps(jcats, indent=4, sort_keys=True)
            content = utils.remove_absolute_paths(content)
            f.write(content)
            self.cacheTime = time.time()

    def loadCacheData(self):
        filename = self.getCacheFile()
        if os.path.exists(filename):
            self.cacheTime = os.path.getmtime(filename)
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                content = utils.restore_absolute_paths(content)
                data = json.loads(content)
                categories = []
                for catj in data:
                    packages = []
                    if 'packages' in catj:
                        for pkgj in catj['packages']:
                            pkg = PackageInfo(**pkgj)
                            packages.append(pkg)
                    cat = PackageCategory(catj['name'], packages)
                    categories.append(cat)
                return categories

    def install(self, pkgName):

        result = None

        # Find package
        pkg = self.findPackageByName(pkgName)

        # Install
        if pkg:
            if pkg.type in ('Workbench', 'Mod'):
                result = self.protocol.installMod(pkg)
            elif pkg.type == 'Macro':
                result = self.protocol.installMacro(pkg)

        # Save meta cache
        if result and result.ok:
            utils.analyse_installed_workbench(pkg)
            savePackageMetadata(pkg)

        return result


class CloudPackageChannel:
    def __init__(self, cid, name, sources):
        self.id = cid
        self.name = name
        self.sources = sources


def getSourcesData():
    path = get_resource_path('data', 'sources.json')
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data


def findCloudChannels():
    channels = []
    data = getSourcesData()
    for channel in data:
        channelId = channel['id']
        channelName = tr(channel['name'])
        sources = []
        for source in channel['sources']:
            sources.append(CloudPackageSource(source, channelId))
        channels.append(CloudPackageChannel(channelId, channelName, sources))
    return channels


def findSource(channelId, name):
    data = getSourcesData()
    for channel in data:
        if channel['id'] == channelId:
            for source in channel['sources']:
                if source['name'] == name:
                    return CloudPackageSource(source, channelId)
