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
import json
import freecad.extman.utils as utils
from freecad.extman import getResourcePath, tr

class PackageCategory:
    
    def __init__(self, name, packages=None):
        self.packages = packages or []
        self.name = name


class PackageInfo:

    def __init__(self, **kw):

        # Defaults
        self.key = None                             # Package identifier
        self.name = None                            # Name
        self.installDir = None                      # where to install
        self.installFile = None                     # for Macros: Path of installed file
        self.basePath = ""                          # for Macros: full root of source file
        self.title = None                           # Displayed name
        self.description = None                     # description
        self.icon = None                            # icon url
        self.iconSources = []                       # List of alternative icons
        self.isCore = False                         # True for all kackages included in FreeCAD
        self.type = 'Mod'                           # Mod, Macro, Workbench
        self.isGit = False                          # is based on git?
        self.isWiki = False                         # is based on wiki?
        self.markedAsSafe = False                   # for Macros: if True, does not ask for confirm
        self.categories = [tr('Uncategorized')]     # Topics/Categories
        self.date = None                            # Last update
        self.version = None                         # Version
        self.git = None                             # Git Repoitory URL
        self.dependencies = None                    # List of dependencies
        self.homepage = None                        # Web
        self.flags = {}                             # py2only, obsolete, banned
        self.readmeUrl = None                       # url of readme
        self.readmeFormat = 'markdown'              # markdown, mediawiki, html
        self.author = None                          # Authors
        self.channelId = None                       # Cloud package source channelId
        self.sourceName = None                      # Cloud package source name

        # Init all with parameters
        for k, v in kw.items():
            setattr(self, k, v)

    def isInstalled(self):

        if self.type in ('Mod', 'Workbench') and self.installDir:
            return os.path.exists(self.installDir)
        
        elif self.type == 'Macro' and self.installFile:
            return os.path.exists(self.installFile)
        
        else:
            return False

    def getIcon(self):

        if not bool(self.icon):
            return 'img/workbench.svg'
        
        elif isinstance(self.icon, str):
            return self.icon
        
        elif isinstance(self.icon, list) and len(self.icon) > 0:
            return self.icon[0]

class PackageSource:

    def __init__(self, sourceType):
        self.type = sourceType
        self.name = None
        self.channelId = None

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
        cache = self.getCategories(cache = True)
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
        for k,v in kwargs.items():
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
    categories.sort(key=lambda c: c.name.lower() if c.name != nocategory and c.name != libcategory and c.name != othercategory else 'zzzz')
    return categories   

def savePackageMetadata(pkg):

    if pkg.type == 'Macro':
        cacheDir = getResourcePath('cache', 'Macro')
        cacheFile = getResourcePath(cacheDir, os.path.basename(pkg.installFile).lower() + ".json")
    elif pkg.type in ('Mod', 'Workbench'):
        cacheDir = getResourcePath('cache', 'Mod')
        cacheFile = getResourcePath(cacheDir, pkg.name + ".json")
    else:
        return None

    if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)

    with open(cacheFile, 'w', encoding='utf-8') as f:
        content = json.dumps(pkg.__dict__, indent=4, sort_keys=True)
        content = utils.removeAbsolutePaths(content)
        f.write(content)
        return None

def loadPackageMetadata(pkg):

    if pkg.type == 'Macro':
        cacheDir = getResourcePath('cache', 'Macro')
        cacheFile = getResourcePath(cacheDir, os.path.basename(pkg.installFile).lower() + ".json")
    elif pkg.type in ('Mod', 'Workbench'):
        cacheDir = getResourcePath('cache', 'Mod')
        cacheFile = getResourcePath(cacheDir, pkg.name + ".json")
    else:
        return False

    if os.path.exists(cacheFile):
        with open(cacheFile, 'r', encoding='utf-8') as f:
            content = f.read()
            content = utils.restoreAbsolutePaths(content)
            data = json.loads(content)
            for k,v in data.items():
                setattr(pkg, k, v)
            return True

    return False
