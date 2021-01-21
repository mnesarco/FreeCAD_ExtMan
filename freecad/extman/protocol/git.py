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

import os
import re
import sys
import tempfile
import traceback
from distutils.version import StrictVersion
from shutil import which
from pathlib import Path
import hashlib
import shutil

import freecad.extman.utils.preferences as pref

from freecad.extman.protocol.manifest import ExtensionManifest
import freecad.extman.protocol.dependencies as deps
import freecad.extman.protocol.fcwiki as fcw
import freecad.extman.protocol.zip as zlib
from freecad.extman import tr, log, get_cache_path, get_macro_path, get_mod_path
from freecad.extman import utils
from freecad.extman.protocol.macro_parser import build_macro_package
from freecad.extman.protocol import Protocol, flags
from freecad.extman.protocol.http import http_get, http_download
from freecad.extman.sources import PackageInfo, InstallResult
from freecad.extman.utils.worker import Worker


MIN_VERSION = StrictVersion('2.14.99')
DISABLE_GIT = False


class SubModulesParser:
    """
    Parses standard .gitmodules files
    """

    PATTERN = re.compile(r"""
        \s*\[\s*submodule\s+(?P<quot>['\"])(?P<module>.*?)(?P=quot)\s*\]
        |
        \s*(?P<var>path|url)\s*=\s*(?P<value>.*)
        """, re.X)

    def __init__(self, content):
        modules = []
        module = {}
        for m in SubModulesParser.PATTERN.finditer(content):
            mod_group = m.group('module')
            var = m.group('var')
            value = m.group('value')
            if mod_group:
                module = {'name': mod_group}
                modules.append(module)
            elif var and module:
                module[var] = value
        self.modules = modules


class GitRepo:

    def __init__(self, url):
        self.url = url
        self.readme = None
        self.manifest = None

    def syncManifestHttp(self):
        ini = self.getRawFile('manifest.ini')
        if not ini:
            ini = self.getRawFile('metadata.txt')
        if ini:
            self.manifest = ExtensionManifest(ini)
            return True

    def syncMetadataHttp(self):
        self.syncManifest()
        self.syncReadme()

    def clone(self, path, **kw):
        return clone_local(self.url, path, **kw)

    def getRawFile(self, path):
        pass

    def getRawFileUrl(self, path=""):
        pass

    def syncReadmeHttp(self):
        pass

    def getZipUrl(self):
        pass

    def asModule(self):
        pass

    def getReadmeUrl(self):
        pass

    def getReadmeFormat(self):
        pass


class GitProtocol(Protocol):

    def __init__(self, repoImpl, url, submodulesUrl, indexType, indexUrl, wikiUrl):
        super().__init__()
        self.url = url
        self.submodulesUrl = submodulesUrl
        self.indexType = indexType
        self.indexUrl = indexUrl
        self.wikiUrl = wikiUrl
        self.repo = repoImpl(url)
        self.RepoImpl = repoImpl

    def getUrl(self):
        return self.url

    def getModList(self):

        # Get index
        index = {}
        if self.indexType == 'wiki' and self.indexUrl and self.wikiUrl:
            index = fcw.get_mod_index(self.indexUrl, self.wikiUrl)

        # Get modules
        if self.submodulesUrl:
            modules = get_submodules(self.submodulesUrl)
            return [self.modFromSubModule(mod, index) for mod in modules]
        else:
            mod = self.repo.asModule()
            if mod:
                return [self.modFromSubModule(mod, index)]
            else:
                return []

    def downloadMacroList(self):

        local_dir = Path(
            get_cache_path(),
            'git',
            str(hashlib.sha256(self.url.encode()).hexdigest()),
            create_dir=True)

        # Try Git
        (gitAvailable, gitExe, gitVersion, gitPython, gitVersionOk) = install_info()
        if gitAvailable and gitPython and gitVersionOk:
            repo, path = clone_local(self.url, path=local_dir)
            return path

        # Try zip/http
        if zlib.is_zip_available():
            zip_path = Path(tempfile.mktemp(suffix=".zip"))
            if http_download(self.repo.getZipUrl(), zip_path):
                exploded = Path(tempfile.mktemp(suffix="_zip"))
                zlib.unzip(zip_path, exploded)
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

    def modFromSubModule(self, mod, index, syncManifest=False, syncReadme=False):

        repo = self.RepoImpl(mod['url'])

        if syncManifest:
            repo.syncManifestHttp()

        if syncReadme:
            repo.syncReadmeHttp()

        icon_path = "resources/icons/{0}.svg".format(mod['name'])

        index_key = mod['url']
        if index_key.endswith('.git'):
            index_key = index_key[:-4]

        indexed = index.get(index_key)
        if indexed:
            icon_path = indexed.get('icon', icon_path)

        if repo.manifest:
            general = repo.manifest.general
            if general and general.iconPath:
                icon_path = repo.manifest.iconPath

        install_dir = Path(get_mod_path(), mod['name'])

        icon_sources = utils.get_workbench_icon_candidates(
            mod['name'],
            repo.getRawFileUrl(),
            icon_path,
            install_dir)

        pkg_info = {
            'name': mod['name'],
            'title': mod['name'],
            'description': None,
            'categories': None,
            'iconSources': icon_sources,
            'readmeUrl': repo.getReadmeUrl(),
            'readmeFormat': repo.getReadmeFormat()
        }

        # Copy data from index
        if indexed:
            pkg_info['title'] = indexed.get('title', pkg_info['title'])
            pkg_info['description'] = indexed.get('description', pkg_info['description'])
            pkg_info['categories'] = indexed.get('categories', pkg_info['categories'])
            pkg_info['author'] = indexed.get('author')
            flag = indexed.get('flag')
            if flag:
                iflags = pkg_info.get('flags', {})
                iflags['obsolete'] = True
                pkg_info['flags'] = iflags

        # Copy all manifest attributes
        if repo.manifest:
            repo.manifest.getData(pkg_info)

        # Override some things
        pkg_info.update(dict(
            key=mod['name'],
            type='Workbench',
            isCore=False,
            installDir=install_dir,
            icon=icon_sources[0],
            categories=utils.get_workbench_categories_from_string(mod['name'], pkg_info['categories']),
            isGit=True,
            git=mod['url']
        ))

        pkg = PackageInfo(**pkg_info)
        flags.apply_predefined_flags(pkg)
        return pkg

    def installMod(self, pkg):

        # Get Git info
        git_available, _, git_version, git_python, git_version_ok = install_info()

        # Get zip info
        zip_available = zlib.is_zip_available()

        # Initialize result
        result = InstallResult(
            gitAvailable=git_available,
            gitPythonAvailable=git_python is not None,
            zipAvailable=zip_available,
            gitVersionOk=git_version_ok,
            gitVersion=git_version
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
        if git_available and git_version_ok and git_python:
            result = self.installModFromGit(pkg, result)

        # Try zip/http install
        elif zip_available:
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
            gh = self.RepoImpl(pkg.git)
            gh.syncManifestHttp()

            # Check dependencies based on manifest.ini or metadata.txt
            (depsOk, failedDependencies) = deps.check_dependencies(gh.manifest)
            if not depsOk:
                result.failedDependencies = failedDependencies
                return result

            # Download master zip
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
                gh = self.RepoImpl(pkg.git)
                gh.syncManifestHttp()

                # Check dependencies based on manifest.ini or metadata.txt
                (depsOk, failedDependencies) = deps.check_dependencies(gh.manifest)
                if not depsOk:
                    result.failedDependencies = failedDependencies
                    return result

                # Clone and update submodules
                repo, _ = clone_local(pkg.git, pkg.installDir, branch='master')
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
                gh = self.RepoImpl(pkg.git)
                gh.syncManifestHttp()

                # Check dependencies based on manifest.ini or metadata.txt
                (depsOk, failedDependencies) = deps.check_dependencies(gh.manifest)
                if not depsOk:
                    result.failedDependencies = failedDependencies
                    return result

                # Upgrade to git if necessary
                import git
                bare_path = Path(pkg.installDir, '.git')
                if not bare_path.exists():
                    bare, _ = gh.clone(bare_path, bare=True)
                    config_set(bare, 'core', 'bare', False)
                    repo = git.Repo(pkg.installDir)
                    repo.head.reset('--hard')

                # Pull
                repo = git.Git(pkg.installDir)
                repo.pull('--depth=1')
                repo = git.Repo(pkg.installDir)
                for mod in repo.submodules:
                    mod.update(init=True, recursive=True)

                result.ok = True

            except:
                log(traceback.format_exc())
                result.ok = False

        return result

    def updateMod(self, pkg):
        return self.installMod(pkg)  # Install handles both cases

    def installMacro(self, pkg):

        (git_available, _, git_version, git_python, git_version_ok) = install_info()

        # Initialize result
        result = InstallResult(
            gitAvailable=git_available,
            gitPythonAvailable=git_python is not None,
            zipAvailable=zlib.is_zip_available(),
            gitVersionOk=git_version_ok,
            gitVersion=git_version
        )

        # Ensure last version if available locally
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


def get_submodules(url):
    """Download and parse .gitmodules from git repository using http"""

    content = http_get(url)
    if content:
        parser = SubModulesParser(content)
        return parser.modules
    else:
        return []


def install_info():
    """
    Returns info about git (installed, executable, version, pygit, git_version_check)
        installed: bool
        executable: path
        version: StrictVersion
        pygit: GitPython module
        git_version_check: bool
    """

    if DISABLE_GIT:
        return False, None, None, None, False

    # Find git executable
    executable = which('git')

    # Check git version
    version_str = None
    if executable:
        with os.popen(executable + ' --version', 'r') as f:
            version_str = f.read()

    # Get strict git version
    version = None
    if version_str:
        result = re.search(r'(\d+\.\d+\.\d+)', version_str)
        if result:
            version = StrictVersion(result.group(1))

    # Get python git module
    try:
        import git
    except ImportError:
        git = None

    installed = bool(version)
    git_version_check = (version and version >= MIN_VERSION)
    return installed, executable, version, git, git_version_check


def update_local(path):
    # Get git
    (gitAvailable, executable, version, pygit, gitVersionOk) = install_info()

    if gitAvailable and pygit and gitVersionOk:
        if Path(path, '.git').exists():

            # Reset
            repo = pygit.Repo(path)
            repo.head.reset('--hard')

            # Pull
            repo = pygit.Git(path)
            repo.pull('--depth=1')
            repo = pygit.Repo(path)
            for submodule in repo.submodules:
                submodule.update(init=True, recursive=True)

            return repo

    return None


def clone_local(repo_url, path=None, **kwargs):
    # Get git
    (gitAvailable, executable, version, pygit, gitVersionOk) = install_info()

    if gitAvailable and pygit and gitVersionOk:

        if path is None:
            path = Path(tempfile.mkdtemp())

        # If exists, reset+pull
        if Path(path, '.git').exists():
            try:
                repo = update_local(path)
                return repo, path
            except:
                #If update_local fails, try clean clone
                traceback.print_exc(file=sys.stderr)
                tmp_path = Path(tempfile.mkdtemp())
                try:
                    repo = pygit.Repo.clone_from(repo_url, tmp_path, depth=1, **kwargs)
                    shutil.rmtree(path, True)
                    shutil.move(tmp_path, path)
                    return repo, path
                except:
                    traceback.print_exc(file=sys.stderr)

        # Clone
        else:
            try:
                repo = pygit.Repo.clone_from(repo_url, path, depth=1, **kwargs)
                return repo, path
            except:
                traceback.print_exc(file=sys.stderr)

    return None, None


def config_set(pyGitRepo, section, option, value):
    cw = None
    try:
        cw = pyGitRepo.config_writer()
        cw.set_value(section, option, value)
    finally:
        try:
            if cw:
                cw.release()
            del cw
        except:
            pass
