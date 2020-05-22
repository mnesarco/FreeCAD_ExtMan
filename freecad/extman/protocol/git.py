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

import json
import os
import re
import sys
import tempfile
import traceback
import xml
from distutils.version import StrictVersion
from shutil import which

from freecad.extman import get_resource_path, log
from freecad.extman.protocol.http import http_get
from freecad.extman.protocol.manifest import ExtensionManifest

MIN_VERSION = StrictVersion('2.14.99')


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

    def getRawFileUrl(self, path):
        pass

    def syncReadmeHttp(self):
        pass

    def getZipUrl(self):
        pass


def get_cache_dir():
    path = get_resource_path('cache')
    if not os.path.exists(path):
        os.mkdir(path)
    return path


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
        if os.path.exists(os.path.join(path, '.git')):

            # Reset
            repo = pygit.Repo(path)
            repo.head.reset('--hard')

            # Pull
            repo = pygit.Git(path)
            repo.pull()
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
            path = tempfile.mkdtemp()

        # If exists, reset+pull
        if os.path.exists(os.path.join(path, '.git')):
            try:
                repo = update_local(path)
                return repo, path
            except:
                traceback.print_exc(file=sys.stderr)

        # Clone
        else:
            try:
                repo = pygit.Repo.clone_from(repo_url, path, **kwargs)
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
