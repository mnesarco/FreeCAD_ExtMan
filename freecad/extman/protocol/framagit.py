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

import re

from freecad.extman.protocol.git import GitProtocol, GitRepo
from freecad.extman.protocol.http import http_get

# Framagit repository URL
REPO_URL = re.compile(r'https://framagit.org/(?P<org>[^/]+)/(?P<repo>[A-Za-z0-9_\-.]+?)(\.git).*', re.I)


class FramagitRepo(GitRepo):

    def __init__(self, url):
        super().__init__(url)
        self.description = None

    def getRawFile(self, path):
        url = self.getRawFileUrl(path)
        return http_get(url)

    def getRawFileUrl(self, path=""):
        url = self.url
        if url.endswith('.git'):
            url = url[:-4]
        return "{0}/-/raw/master/{1}".format(url, path)

    def syncReadmeHttp(self):
        readme = self.getRawFile('README.md')
        if readme:
            self.readme = readme

    def getZipUrl(self):
        url = self.url
        if url.endswith('.git'):
            url = url[:-4]
        rep = REPO_URL.search(self.url)
        if rep:
            return "{0}/-/archive/{1}-master.zip".format(url.strip('/'), rep.group('repo'))
        else:
            return None

    def asModule(self):
        repo_url = REPO_URL.search(self.url)
        if repo_url:
            name = repo_url.group('repo')
            return {
                'name': name,
                'path': name,
                'url': self.url
                }
        else:
            return None

    def getReadmeUrl(self):
        url = self.url
        if url.endswith('.git'):
            url = url[:-4]
        return url.strip('/') + '/-/blob/master/README.md'

    def getReadmeFormat(self):
        return 'html'


class FramagitProtocol(GitProtocol):
    def __init__(self, url, submodulesUrl, indexType, indexUrl, wikiUrl):
        super().__init__(FramagitRepo, url, submodulesUrl, indexType, indexUrl, wikiUrl)

