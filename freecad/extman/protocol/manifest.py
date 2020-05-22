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

import configparser

from freecad.extman import log
from freecad.extman import utils


class ManifestSection:

    def __init__(self, items):
        for item, value in items:
            self.__setattr__(item, utils.SanitizedHtml(value))

    def __getattr__(self, attr):
        return None

    def getValues(self):
        return self.__dict__.items()


class ExtensionManifest:

    def __init__(self, content):
        try:
            parser = configparser.ConfigParser()
            parser.read_string(content)
            for section, items in parser.items():
                self.__setattr__(section, ManifestSection(items.items()))
        except:
            log("Invalid manifest file")

    def __getattr__(self, attr):
        return ManifestSection([])

    def getSections(self):
        return self.__dict__.items()

    def getData(self, info):

        """Update info dict with self data"""

        for name, data in self.getSections():
            if name == 'general':
                info.update(data.__dict__)
                categories = info.get('categories')
                if categories:
                    if isinstance(categories, str):
                        info['categories'] = utils.CommaStringList(categories)
            elif name in ('dependencies', 'install'):
                info[name] = dict(data.__dict__)
            elif name == 'git':
                info['gitManifest'] = dict(data.__dict__)
