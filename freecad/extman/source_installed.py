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
import configparser as cp
import json
import os

import freecad.extman.protocol.github as gh
from freecad.extman import flags
from freecad.extman import get_resource_path, tr
from freecad.extman import utils
from freecad.extman.macro_parser import build_macro_package
from freecad.extman.protocol.manifest import ExtensionManifest
from freecad.extman.sources import PackageInfo, PackageSource, PackageCategory, groupPackagesInCategories, \
    savePackageMetadata, loadPackageMetadata


class InstalledPackageSource(PackageSource):

    def __init__(self):
        super().__init__('Installed')
        self.coreModDir = os.path.join(App.getResourceDir(), 'Mod')
        self.userModDir = os.path.join(App.getUserAppDataDir(), 'Mod')
        self.userMacroDir = App.getUserMacroDir(True)
        self.workbenches = Gui.listWorkbenches()
        self.updates = {}
        self.showCorePackages = True

    def getTitle(self):
        return tr('Installed packages')

    def getDescription(self):
        return tr('All installed packages')

    def getIcon(self):
        return utils.path_to_url(get_resource_path('html', 'img', 'source_installed.svg'))

    def getPackages(self, cache=True):
        packages = []
        # Add Core Mods
        if self.showCorePackages:
            packages.extend(self.importMods(self.coreModDir, True))
        # Add User Mods
        packages.extend(self.importMods(self.userModDir))
        # Add User Macros
        packages.extend(self.importMacros(self.userMacroDir))
        # Sort all
        packages.sort(key=lambda p: p.title.lower())
        return packages

    def getCategories(self, cache=True):
        categories = groupPackagesInCategories(self.getPackages())
        return categories

    def importMods(self, path, isCore=False):
        packages = []
        if os.path.exists(path):
            for pdir in os.listdir(path):
                if pdir != 'ExtMan':
                    pkg = self.importMod(path, pdir, isCore)
                    if pkg: packages.append(pkg)
        return packages

    def importMacros(self, path, isCore=False):
        packages = []
        if os.path.exists(path):
            for pfile in os.listdir(path):
                ppath = os.path.join(path, pfile)
                if os.path.isfile(ppath):
                    pkg = self.importMacro(ppath, pfile, isCore)
                    if pkg:
                        packages.append(pkg)
        return packages

    def importMacro(self, path, pfile, isCore=False):
        lname = pfile.lower()
        if lname.endswith('.fcmacro'):
            macro = build_macro_package(path, pfile, isCore)
            flags.apply_predefined_flags(macro)
            analyseInstalledMacro(macro)
            return macro

    def importMod(self, path, pdir, isCore):
        installDir = os.path.join(path, pdir)
        if os.path.isdir(installDir):
            wbKey = utils.get_workbench_key(pdir)
            wb = self.workbenches.get(wbKey)
            pkg = PackageInfo(
                key=wbKey,
                type='Workbench' if wb else 'Mod',
                name=pdir,
                isCore=isCore,
                installDir=installDir,
                icon=self.getModIcon(pdir, installDir, wbKey, wb),
                title=wb.MenuText if wb else pdir,
                description=wb.ToolTip if wb else pdir,
                categories=utils.get_workbench_categories(wb),
                isGit=os.path.isdir(os.path.join(installDir, '.git'))
            )
            flags.apply_predefined_flags(pkg)
            analyseInstalledMod(pkg)
            return pkg

    def getModIcon(self, name, installDir, wbKey, wb):
        iconPath = os.path.join(installDir, 'Resources', 'icons', '{0}Workbench.svg'.format(name))
        if os.path.exists(iconPath):
            return utils.path_to_url(iconPath)
        else:
            if wb and hasattr(wb, 'Icon'):
                return utils.path_to_url(utils.extract_icon(wb.Icon, 'workbench.svg'))
        return utils.path_to_url(get_resource_path('html', 'img', 'workbench.svg'))

    def getUpdates(self, package):
        return self.updates.get(package)

    def install(self, pkg):
        return None


def analyseInstalledMod(pkg):
    # Return cache if available
    if loadPackageMetadata(pkg):
        return pkg

    # If no cache available
    analyseGit(pkg)
    analyseManifest(pkg)
    analyseInit(pkg)
    analyseInitGui(pkg)
    analyseReadme(pkg)
    savePackageMetadata(pkg)
    return pkg


def analyseGit(pkg):
    gitDir = os.path.join(pkg.installDir, '.git')
    if os.path.exists(gitDir):
        parser = cp.ConfigParser()
        parser.read(os.path.join(gitDir, 'config'))
        if parser.has_option('remote "origin"', 'url'):
            url = parser['remote "origin"']['url']
            if url:
                pkg.git = url
                pkg.isGit = True


def analyseManifest(pkg):
    mfile = os.path.join(pkg.installDir, 'manifest.ini')

    if not os.path.exists(mfile):
        mfile = os.path.join(pkg.installDir, 'metadata.txt')

    if os.path.exists(mfile):
        with open(mfile, 'r', encoding='utf-8') as f:
            manifest = ExtensionManifest(f.read())
            data = {}
            manifest.getData(data)
            for k, v in data.items():
                setattr(pkg, k, v)


def analyseReadme(pkg):
    mfile = os.path.join(pkg.installDir, 'README.md')
    if os.path.exists(mfile) and pkg.git:
        if 'github.com' in pkg.git:
            ghr = gh.GithubRepo(pkg.git)
            pkg.readmeUrl = ghr.getRawFileUrl('README.md')
            pkg.readmeFormat = 'markdown'


def analyseInit(pkg):
    pass


def analyseInitGui(pkg):
    utils.analyse_installed_workbench(pkg)


def analyseInstalledMacro(pkg):
    if not loadPackageMetadata(pkg):
        savePackageMetadata(pkg)
    return pkg
