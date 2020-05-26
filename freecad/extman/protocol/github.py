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
import hashlib
import os
import shutil
import tempfile
import traceback
from pathlib import Path
from html import unescape
from html.parser import HTMLParser

import freecad.extman.protocol.dependencies as deps
import freecad.extman.utils.preferences as pref
import freecad.extman.protocol.fcwiki as fcw
import freecad.extman.protocol.git as egit
import freecad.extman.protocol.zip as zlib
from freecad.extman import get_resource_path, tr, log, get_cache_path, get_macro_path, get_mod_path
from freecad.extman import utils
from freecad.extman.protocol.macro_parser import build_macro_package
from freecad.extman.protocol import Protocol, flags
from freecad.extman.protocol.http import http_get, http_download
from freecad.extman.sources import PackageInfo, InstallResult
from freecad.extman.utils.worker import Worker


class ReadmeParser(HTMLParser):

    def error(self, message):
        pass

    def __init__(self, meta_filter=None):
        super().__init__()
        self.html = None
        self.meta = {}
        self.inContent = False
        self.meta_filter = meta_filter

    def handle_starttag(self, tag, attrs):
        if self.inContent:
            text = "<{0} ".format(tag)
            for attName, attVal in attrs:
                text += "{0}=\"{1}\" ".format(attName, attVal)
            text += '>'
            self.html += text

        elif tag == 'meta':
            meta = dict(attrs)
            name = meta.get('name', meta.get('property'))
            if self.meta_filter is None:
                self.meta[name] = meta.get('content')
            else:
                if name in self.meta_filter:
                    self.meta[name] = meta.get('content')

        elif tag == 'article':
            self.inContent = True
            self.html = ''

    def handle_endtag(self, tag):
        if self.inContent:
            self.html += "</{0}>".format(tag)
        elif tag == 'article':
            self.inContent = False

    def handle_data(self, data):
        if self.inContent:
            self.html += unescape(data).replace(b'\xc2\xa0'.decode("utf-8"), ' ')


class GithubRepo(egit.GitRepo):

    def __init__(self, url):
        super().__init__(url)
        self.description = None

    def getRawFile(self, path):
        url = self.getRawFileUrl(path)
        return http_get(url)

    def getRawFileUrl(self, path=""):
        url = self.url.replace('github.com', 'raw.githubusercontent.com')
        if url.endswith('.git'):
            url = url[:-4]
        return "{0}/master/{1}".format(url, path)

    def syncReadmeHttp(self):
        readme = self.getRawFile('README.md')
        if readme:
            parser = ReadmeParser(['og:description'])
            parser.feed(readme)
            self.description = parser.meta.get('og:description')
            self.readme = parser.html

    def getZipUrl(self):
        url = self.url
        if url.endswith('.git'):
            url = url[:-4]
        return url.strip('/') + "/archive/master.zip"


class GithubProtocol(Protocol):

    def __init__(self, url, submodulesUrl, indexType, indexUrl, wikiUrl):
        super().__init__()
        self.url = url
        self.submodulesUrl = submodulesUrl
        self.indexType = indexType
        self.indexUrl = indexUrl
        self.wikiUrl = wikiUrl

    def getModList(self):

        # Get index
        index = {}
        if self.indexType == 'wiki' and self.indexUrl and self.wikiUrl:
            index = fcw.get_mod_index(self.indexUrl, self.wikiUrl)

        # Get modules
        if self.submodulesUrl:
            modules = egit.get_submodules(self.submodulesUrl)
            return [self.modFromSubModule(subm, index) for subm in modules]
        else:
            return []

    def downloadMacroList(self):

        local_dir = Path(
            get_cache_path(),
            'git',
            str(hashlib.sha256(self.url.encode()).hexdigest()),
            create_dir=True)

        # Try Git
        (gitAvailable, gitExe, gitVersion, gitPython, gitVersionOk) = egit.install_info()
        if gitAvailable and gitPython and gitVersionOk:
            repo, path = egit.clone_local(self.url, path=local_dir)
            return path

        # Try zip/http
        if zlib.is_zip_available():
            gh = GithubRepo(self.url)
            zippath = Path(tempfile.mktemp(suffix=".zip"))
            if http_download(gh.getZipUrl(), zippath):
                exploded = Path(tempfile.mktemp(suffix="_zip"))
                zlib.unzip(zippath, exploded)
                # Remove old if exists
                if local_dir.exists():
                    shutil.rmtree(local_dir, ignore_errors=True)
                # Move exploded dir to install dir
                for entry_path in exploded.iterdir():
                    if entry_path.is_dir():
                        shutil.move(entry_path, local_dir)
                        return local_dir

    def getMacroList(self):
        install_dir = get_macro_path()
        macros = []
        path = self.downloadMacroList()
        if path:
            workers = []
            for entry in path.glob('**/*'):
                if '.git' in entry.name.lower():
                    continue
                if entry.name.lower().endswith('.fcmacro'):
                    worker = Worker(build_macro_package,
                                    entry,
                                    entry.stem,
                                    is_git=True,
                                    install_path=Path(install_dir, entry.name),
                                    base_path=entry.relative_to(path).parent)
                    worker.start()
                    workers.append(worker)
            macros = [flags.apply_predefined_flags(w.get()) for w in workers]
        return macros

    def modFromSubModule(self, subm, index, syncManifest=False, syncReadme=False):

        repo = GithubRepo(subm['url'])

        if syncManifest:
            repo.syncManifestHttp()

        if syncReadme:
            repo.syncReadmeHttp()

        iconPath = "Resources/icons/{0}Workbench.svg".format(subm['name'])

        indexKey = subm['url']
        if indexKey.endswith('.git'):
            indexKey = indexKey[:-4]

        indexed = index.get(indexKey)
        if indexed:
            iconPath = indexed.get('icon', iconPath)

        if repo.manifest:
            general = repo.manifest.general
            if general and general.iconPath:
                iconPath = repo.manifest.iconPath

        installDir = Path(get_mod_path(), subm['name'])

        iconSources = utils.get_workbench_icon_candidates(
            subm['name'],
            repo.getRawFileUrl(),
            iconPath,
            installDir)

        pkgInfo = {
            'name': subm['name'],
            'title': subm['name'],
            'description': None,
            'categories': None,
            'iconSources': iconSources,
            'readmeUrl': repo.getRawFileUrl('README.md'),
            'readmeFormat': 'markdown'
        }

        # Copy data from index              
        if indexed:
            pkgInfo['title'] = indexed.get('title', pkgInfo['title'])
            pkgInfo['description'] = indexed.get('description', pkgInfo['description'])
            pkgInfo['categories'] = indexed.get('categories', pkgInfo['categories'])
            pkgInfo['author'] = indexed.get('author')
            flag = indexed.get('flag')
            if flag:
                iflags = pkgInfo.get('flags', {})
                iflags['obsolete'] = True
                pkgInfo['flags'] = iflags

        # Copy all manifest attributes
        if repo.manifest:
            repo.manifest.getData(pkgInfo)

        # Override some things
        pkgInfo.update(dict(
            key=subm['name'],
            type='Workbench',
            isCore=False,
            installDir=installDir,
            icon=iconSources[0],
            categories=utils.get_workbench_categories_from_string(subm['name'], pkgInfo['categories']),
            isGit=True,
            git=subm['url']
        ))

        pkg = PackageInfo(**pkgInfo)
        flags.apply_predefined_flags(pkg)
        return pkg

    def installMod(self, pkg):

        # Get Git info
        (gitAvailable, gitExe, gitVersion, gitPython, gitVersionOk) = egit.install_info()

        # Get zip info
        zipAvailable = zlib.is_zip_available()

        # Initialize result
        result = InstallResult(
            gitAvailable=gitAvailable,
            gitPythonAvailable=gitPython is not None,
            zipAvailable=zipAvailable,
            gitVersionOk=gitVersionOk,
            gitVersion=gitVersion
        )

        # Check valid install dir
        in_mods = get_mod_path() == pkg.installDir.parent
        in_macros = pkg.installFile and get_macro_path() in pkg.installFile.parents
        if not in_mods and not in_macros:
            log('Invalid install dir: {0}'.format(pkg.installDir))
            result.ok = False
            result.invalidInstallDir = True
            return result

        # Try Git install
        if gitAvailable and gitVersionOk and gitPython:
            result = self.installModFromGit(pkg, result)

        # Try zip/http install
        elif zipAvailable:
            result = self.installModFromHttpZip(pkg, result)

        if result.ok:
            try:
                self.linkMacrosFromMod(pkg)
            except:
                # ! TODO: Rollback everything if macro links fail?
                pass

        return result

    def installModFromHttpZip(self, pkg, result):

        try:
            # Init repo, get manifest            
            gh = GithubRepo(pkg.git)
            gh.syncManifestHttp()

            # Check dependencies based on manifets.ini or metadata.txt
            (depsOk, failedDependencies) = deps.check_dependencies(gh.manifest)
            if not depsOk:
                result.failedDependencies = failedDependencies
                return result

            # Download mater zip
            zip_path = Path(tempfile.mktemp(suffix=".zip"))
            if http_download(gh.getZipUrl(), zip_path):
                exploded = Path(tempfile.mktemp(suffix="_zip"))
                zlib.unzip(zip_path, exploded)

                # Remove old if exists
                if pkg.installDir.exists():
                    shutil.rmtree(pkg.installDir, ignore_errors=True)

                # Move exploded dir to install dir
                for entry_path in exploded.iterdir():
                    if entry_path.is_dir():
                        shutil.move(entry_path, pkg.installDir)
                        result.ok = True
                        break  # Only one zip directory is expected

        except:
            log(traceback.format_exc())
            result.ok = False

        return result

    def installModFromGit(self, pkg, result):

        # Update instead if already exists
        if pkg.installDir.exists():
            return self.updateModFromGit(pkg, result)

        # Install
        else:

            try:
                # Init repo, get manifest            
                gh = GithubRepo(pkg.git)
                gh.syncManifestHttp()

                # Check dependencies based on manifets.ini or metadata.txt
                (depsOk, failedDependencies) = deps.check_dependencies(gh.manifest)
                if not depsOk:
                    result.failedDependencies = failedDependencies
                    return result

                # Clone and update submudules
                repo, repoPath = egit.clone_local(pkg.git, pkg.installDir, branch='master')
                if repo.submodules:
                    repo.submodule_update(recursive=True)

                result.ok = True

            except:
                log(traceback.format_exc())
                result.ok = False

        return result

    def updateModFromGit(self, pkg, result):

        # Install instead if not exists
        if not pkg.installDir.exists():
            return self.installModFromGit(pkg, result)

        # Update
        else:

            try:
                # Init repo, get manifest            
                gh = GithubRepo(pkg.git)
                gh.syncManifestHttp()

                # Check dependencies based on manifets.ini or metadata.txt
                (depsOk, failedDependencies) = deps.check_dependencies(gh.manifest)
                if not depsOk:
                    result.failedDependencies = failedDependencies
                    return result

                # Upgrade to git if necessary
                import git
                bare_path = Path(pkg.installDir, '.git')
                if not bare_path.exists():
                    bare, _ = gh.clone(bare_path, bare=True)
                    egit.config_set(bare, 'core', 'bare', False)
                    repo = git.Repo(pkg.installDir)
                    repo.head.reset('--hard')

                # Pull
                repo = git.Git(pkg.installDir)
                repo.pull()
                repo = git.Repo(pkg.installDir)
                for subm in repo.submodules:
                    subm.update(init=True, recursive=True)

                result.ok = True

            except:
                log(traceback.format_exc())
                result.ok = False

        return result

    def updateMod(self, pkg):
        return self.installMod(pkg)  # Install handles both cases

    def installMacro(self, pkg):

        (gitAvailable, gitExe, gitVersion, gitPython, gitVersionOk) = egit.install_info()

        # Initialize result
        result = InstallResult(
            gitAvailable=gitAvailable,
            gitPythonAvailable=gitPython is not None,
            zipAvailable=zlib.is_zip_available(),
            gitVersionOk=gitVersionOk,
            gitVersion=gitVersion
        )

        # Ensure last version it available locally
        src_dir = self.downloadMacroList()

        # Get path of source macro file
        src_file = Path(src_dir, pkg.basePath, pkg.installFile.name)

        # Copy Macro
        files = []
        try:

            macros_dir = get_macro_path()
            if not macros_dir.exists():
                macros_dir.mkdir(parents=True)

            log('Installing', pkg.installFile)

            shutil.copy2(src_file, pkg.installFile)
            files.append(pkg.installFile)

            # Copy files
            if pkg.files:
                for f in pkg.files:

                    file_base_path = utils.path_relative(f)
                    dst = Path(pkg.installDir, file_base_path).absolute()
                    src = Path(src_dir, pkg.basePath, file_base_path).absolute()

                    log('Installing ', dst)

                    if pkg.installDir not in dst.parents:
                        result.message = tr('Macro package attempts to install files outside of permitted path')
                        raise Exception()

                    if src_dir not in src.parents:
                        result.message = tr('Macro package attempts to access files outside of permitted path')
                        raise Exception()

                    dst_dir = dst.parent
                    if dst_dir != pkg.installDir and dst_dir not in files and not dst_dir.exists():
                        dst_dir.mkdir(parents=True)
                        files.append(dst_dir)

                    shutil.copy2(src, dst)
                    files.append(dst)

            result.ok = True

        except:

            log(traceback.format_exc())

            result.ok = False
            if not result.message:
                result.message = tr('Macro was not installed, please contact the maintainer.')

            # Rollback
            files.sort(reverse=True)
            for f in files:
                try:
                    log("Rollback ", f)
                    if f.is_file():
                        f.unlink()
                    elif f.is_dir():
                        shutil.rmtree(f, ignore_errors=True)
                except:
                    log(traceback.format_exc())

        return result

    def updateMacro(self, pkg):
        pass

    def linkMacrosFromMod(self, pkg):

        # Ensure macro dir
        macros = get_macro_path()
        if not macros.exists():
            macros.mkdir(parents=True)

        # Search and link
        if pkg.installDir.exists():
            for f in pkg.installDir.iterdir():
                if f.name.lower().endswith(".fcmacro"):
                    Path(macros, f.name).symlink_to(f)
                    pref.set_plugin_parameter(pkg.name, 'destination', str(pkg.installDir))
