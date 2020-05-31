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
from html import unescape
from html.parser import HTMLParser

from freecad.extman.protocol.git import GitProtocol, GitRepo
from freecad.extman.protocol.http import http_get

# Github repository URL
REPO_URL = re.compile(r'https://github.com/(?P<org>[^/]+)/(?P<repo>[A-Za-z0-9_\-.]+?)(\.git).*', re.I)


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


class GithubRepo(GitRepo):

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


class GithubProtocol(GitProtocol):
    def __init__(self, url, submodulesUrl, indexType, indexUrl, wikiUrl):
        super().__init__(GithubRepo, url, submodulesUrl, indexType, indexUrl, wikiUrl)

