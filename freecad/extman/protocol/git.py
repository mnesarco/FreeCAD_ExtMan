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

import sys
import os
import json
import re
import xml

from distutils.version import StrictVersion
from freecad.extman import getResourcePath, log
from freecad.extman.protocol.manifest import ExtensionManifest
from freecad.extman.protocol.http import httpGet

#------------------------------------------------------------------------------
MIN_VERSION = StrictVersion('2.14.99')

#------------------------------------------------------------------------------
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
            modg = m.group('module')
            var = m.group('var')
            value = m.group('value')
            if modg:
                module = { 'name': modg }
                modules.append(module)
            elif var and module:
                module[var] = value
        self.modules = modules

#------------------------------------------------------------------------------
def getCacheDir():
    path = getResourcePath('cache')
    if not os.path.exists(path):
        os.mkdir(path)
    return path

#------------------------------------------------------------------------------
def getSubModules(url):
    content = httpGet(url)
    if content:
        parser = SubModulesParser(content)
        return parser.modules
    else:
        return []

#------------------------------------------------------------------------------
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
        return cloneLocal(self.url, path, **kw)

    def getRawFile(self, path):
        pass

    def getRawFileUrl(self, path):
        pass

    def syncReadmeHttp(self):
        pass

    def getZipUrl(self):
        pass


#------------------------------------------------------------------------------
def install_info():
    
    """
    Returns info about git (installed, executable, version, pygit, git_version_check)
        installed: bool
        executable: path
        version: StrictVersion
        pygit: python module
        git_version_check: bool
    """

    # Find git executable
    from shutil import which
    executable = which('git')

    # Check git version
    versionStr = None
    if executable:
        with os.popen(executable + ' --version', 'r') as f:
            versionStr = f.read()

    # Get strict git version
    version = None
    if versionStr:
        result = re.search(r'(\d+\.\d+\.\d+)', versionStr)
        if result:
            version = StrictVersion(result.group(1))
    
    # Get python git module
    try:
        import git
    except ImportError:
        git = None

    installed = bool(version)
    return (installed, executable, version, git, (version and version >= MIN_VERSION))

#------------------------------------------------------------------------------
def updateLocal(path):

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
            for subm in repo.submodules:
                subm.update(init=True, recursive=True)

            return repo

    return None

#------------------------------------------------------------------------------
def cloneLocal(repoUrl, path = None, **kwargs):
    
    # Get git
    (gitAvailable, executable, version, pygit, gitVersionOk) = install_info()

    if gitAvailable and pygit and gitVersionOk:

        if path is None:
            import tempfile
            path = tempfile.mkdtemp()
    
        # If exists, reset+pull
        if os.path.exists(os.path.join(path, '.git')):
            try:
                repo = updateLocal(path)
                return (repo, path)
            except:
                import traceback
                traceback.print_exc(file=sys.stderr)

        # Clone
        else:
            try:
                repo = pygit.Repo.clone_from(repoUrl, path, **kwargs)
                return (repo, path)
            except:
                import traceback
                traceback.print_exc(file=sys.stderr)
    
    return (None, None)

#------------------------------------------------------------------------------
def configSet(pyGitRepo, section, option, value):

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