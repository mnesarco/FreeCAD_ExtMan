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

import json
from pathlib import Path

import freecad.extman.utils as utils
from freecad.extman import tr, get_cache_path


class PackageCategory:

    def __init__(self, name, packages=None):
        self.packages = packages or []
        self.name = name


class PackageInfo:

    def __init__(self, **kw):

        # Defaults
        self.key = None  # Package identifier
        self.name = None  # Name
        self.installDir = None  # where to install
        self.installFile = None  # for Macros: Path of installed file
        self.basePath = ""  # for Macros: full root of source file
        self.title = None  # Displayed name
        self.description = None  # description
        self.icon = None  # icon url
        self.iconSources = []  # List of alternative icons
        self.isCore = False  # True for all packages included in FreeCAD
        self.type = 'Mod'  # Mod, Macro, Workbench
        self.isGit = False  # is based on git?
        self.isWiki = False  # is based on wiki?
        self.markedAsSafe = False  # for Macros: if True, does not ask for confirm
        self.categories = [tr('Uncategorized')]  # Topics/Categories
        self.date = None  # Last update
        self.version = None  # Version
        self.git = None  # Git Repoitory URL
        self.dependencies = None  # List of dependencies
        self.homepage = None  # Web
        self.flags = {}  # py2only, obsolete, banned
        self.readmeUrl = None  # url of readme
        self.readmeFormat = 'markdown'  # markdown, mediawiki, html
        self.author = None  # Authors
        self.channelId = None  # Cloud package source channelId
        self.sourceName = None  # Cloud package source name

        # Init all with parameters
        for k, v in kw.items():
            setattr(self, k, v)

    def isInstalled(self):

        if self.type in ('Mod', 'Workbench') and self.installDir:
            return Path(self.installDir).exists()

        elif self.type == 'Macro' and self.installFile:
            return Path(self.installFile).exists()

        else:
            return False

    def getIcon(self):

        if not bool(self.icon):
            return 'img/workbench.svg'

        elif isinstance(self.icon, str):
            return self.icon

        elif isinstance(self.icon, list) and len(self.icon) > 0:
            return self.icon[0]

    def toSerializable(self):
        serializable = {}
        for k, v in self.__dict__.items():
            if isinstance(v, (int, str, float, bool, list, dict)):
                serializable[k] = v
            elif v is None:
                serializable[k] = v
            else:
                serializable[k] = str(v)
        return serializable

    @staticmethod
    def fromSerializable(serializable):
        data = {}
        for k, v in serializable.items():
            if k in ('installDir', 'installFile'):
                if v:
                    data[k] = Path(v)
                else:
                    data[k] = None
            else:
                data[k] = v
        return PackageInfo(**data)


class PackageSource:

    def __init__(self, sourceType):
        self.type = sourceType
        self.name = None
        self.channelId = None
        self.isInstalledSource = False

    def getTitle(self):
        return 'Unknown'

    def getDescription(self):
        return 'Unknown'

    def getIcon(self):
        return 'img/package_source.svg'

    def getPackages(self, cache=True):
        return []

    def getCategories(self, cache=True):
        return []

    def getUpdates(self, package):
        return False

    def install(self, pkgName):
        pass

    def updatePackageList(self):
        pass

    def getReadmeUrl(self, pkg):
        pass

    def findPackageByName(self, name):
        cache = self.getCategories(cache=True)
        for cat in cache:
            pkg = next((p for p in cat.packages if p.name == name), None)
            if pkg:
                return pkg


class UnsupportedSourceException(Exception):
    pass


class InstallResult:

    def __init__(self, **kwargs):
        self.gitAvailable = False
        self.gitPythonAvailable = False
        self.zipAvailable = False
        self.gitVersionOk = False
        self.gitVersion = None
        self.failedDependencies = []
        self.invalidInstallDir = False
        self.ok = False
        self.message = None
        for k, v in kwargs.items():
            setattr(self, k, v)


def groupPackagesInCategories(packages):
    nocategory = tr('Uncategorized').lower()
    libcategory = tr('Libraries').lower()
    othercategory = tr('Other').lower()
    categories = {}

    for pkg in packages:
        pcats = pkg.categories
        if pcats:
            if pkg.type == 'Mod' and len(pcats) == 1 and pcats[0] == nocategory:
                pcats = [libcategory]

            for pcat in pcats:
                cat = categories.get(pcat)
                if not cat:
                    cat = PackageCategory(pcat)
                    categories[pcat] = cat
                cat.packages.append(pkg)

    categories = list(categories.values())
    categories.sort(key=lambda
        c: c.name.lower() if c.name != nocategory and c.name != libcategory and c.name != othercategory else 'zzzz')
    return categories


def savePackageMetadata(pkg):

    if pkg.type == 'Macro':
        cache_dir = Path(get_cache_path(), 'Macro')
        cache_file = Path(cache_dir, Path(pkg.installFile).stem.lower() + '.json')
    elif pkg.type in ('Mod', 'Workbench'):
        cache_dir = Path(get_cache_path(), 'Mod')
        cache_file = Path(cache_dir, pkg.name + ".json")
    else:
        return None

    if not cache_dir.exists():
        cache_dir.mkdir(parents=True)

    with open(cache_file, 'w', encoding='utf-8') as f:
        content = json.dumps(pkg.toSerializable(), indent=4, sort_keys=True)
        content = utils.remove_absolute_paths(content)
        f.write(content)
        return None


def loadPackageMetadata(pkg):

    if pkg.type == 'Macro':
        cache_dir = Path(get_cache_path(), 'Macro')
        cache_file = Path(cache_dir, Path(pkg.installFile).stem.lower() + '.json')
    elif pkg.type in ('Mod', 'Workbench'):
        cache_dir = Path(get_cache_path(), 'Mod')
        cache_file = Path(cache_dir, pkg.name + ".json")
    else:
        return False

    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            content = utils.restore_absolute_paths(content)
            data = json.loads(content)
            for k, v in data.items():
                if k in ('installDir', 'installFile'):
                    if v:
                        setattr(pkg, k, Path(v))
                    else:
                        setattr(pkg, k, None)
                else:
                    setattr(pkg, k, v)
            return True

    return False
