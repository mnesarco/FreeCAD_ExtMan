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

import shutil

from git.objects import base
import FreeCAD as App
import FreeCADGui as Gui
import configparser as cp
import os, ast
from pathlib import Path

import freecad.extman.protocol.github as gh
from freecad.extman.protocol import flags
from freecad.extman import get_resource_path, log, log_err, tr, get_macro_path, get_mod_path, get_freecad_resource_path
from freecad.extman import utils
from freecad.extman.protocol.macro_parser import build_macro_package
from freecad.extman.protocol.manifest import ExtensionManifest
from freecad.extman.sources import (
    PackageInfo, PackageSource, groupPackagesInCategories,
    savePackageMetadata, loadPackageMetadata)


class InstalledPackageSource(PackageSource):

    def __init__(self):
        super().__init__('Installed')
        self.coreModDir = Path(get_freecad_resource_path(), 'Mod')
        self.userModDir = get_mod_path()
        self.userMacroDir = get_macro_path()
        self.workbenches = Gui.listWorkbenches()
        self.updates = {}
        self.showCorePackages = True
        self.name = "Installed"
        self.channelId = "InstalledPackages"
        self.isInstalledSource = True

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
        if path.exists():
            for pkg_dir in path.iterdir():
                if pkg_dir.stem != 'ExtMan':
                    pkg = self.importMod(path, pkg_dir, isCore)
                    if pkg:
                        packages.append(pkg)
        return packages

    def importMacros(self, path, isCore=False):
        packages = []
        if path.exists():
            for macro_path in path.iterdir():
                if macro_path.is_file():
                    pkg = self.importMacro(macro_path, macro_path.name, isCore)
                    if pkg:
                        packages.append(pkg)
        return packages

    def importMacro(self, path, file_name, isCore=False):
        lname = file_name.lower()
        if lname.endswith('.fcmacro'):
            macro = build_macro_package(path, file_name, isCore, install_path=path)
            flags.apply_predefined_flags(macro)
            analyseInstalledMacro(macro)
            return macro

    def importMod(self, path, installDir, isCore):
        pdir = installDir.name
        if installDir.is_dir():
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
                isGit=Path(installDir, '.git').is_dir()
            )
            flags.apply_predefined_flags(pkg)
            analyseInstalledMod(pkg)
            return pkg

    def getModIcon(self, name, install_path, wbKey, wb):
        icon_path = Path(install_path, 'resources', 'icons', '{0}Workbench.svg'.format(name))
        if icon_path.exists():
            return utils.path_to_url(icon_path)
        else:
            if wb and hasattr(wb, 'Icon'):
                return utils.path_to_url(utils.extract_icon(wb.Icon, 'workbench.svg'))
        return utils.path_to_url(get_resource_path('html', 'img', 'workbench.svg'))

    def getUpdates(self, package):
        return self.updates.get(package)

    def install(self, pkg):
        return None

    def uninstall(self, pkg):
        log("Uninstalling {}".format(pkg.name))
        try:
            if hasattr(pkg, 'installFile') and pkg.type == 'Macro':
                uninstall_macro(pkg.installFile)
            elif hasattr(pkg, 'installDir') and pkg.type == 'Workbench':
                shutil.rmtree(pkg.installDir, ignore_errors=True)                
        except BaseException as e:
            log_err(str(e))


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
    git_dir = Path(pkg.installDir, '.git')
    if git_dir.exists():
        parser = cp.ConfigParser()
        parser.read(Path(git_dir, 'config'))
        if parser.has_option('remote "origin"', 'url'):
            url = parser['remote "origin"']['url']
            if url:
                pkg.git = url
                pkg.isGit = True


def analyseManifest(pkg):
    manifest_file = Path(pkg.installDir, 'manifest.ini')

    if not manifest_file.exists():
        manifest_file = Path(pkg.installDir, 'metadata.txt')

    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = ExtensionManifest(f.read())
            data = {}
            manifest.getData(data)
            for k, v in data.items():
                setattr(pkg, k, v)


def analyseReadme(pkg):
    readme_file = Path(pkg.installDir, 'README.md')
    if readme_file.exists() and pkg.git:
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


def get_macro_files(path):
    base_dir = Path(path.parent)
    files = [path]
    with open(path, 'r') as f:
        src = ast.parse(f.read(), str(path), 'exec')
        for node in src.body:
            if isinstance(node, ast.Assign) and node.targets[0].id == '__Files__':
                names = node.value.s.split(",")
                for name in names:
                    files.append(base_dir / name)
                break
    return files


def uninstall_macro(path):
    dirs = set()  
    macros = get_macro_path()
    for file in get_macro_files(path):
        if file.exists():
            if file.is_file():
                os.remove(file)
                dirs.add(Path(file.parent))
            elif file.is_dir():
                dirs.append(file)
    for d in dirs:
        if not os.listdir(d) and d != macros:
            os.rmdir(d)
