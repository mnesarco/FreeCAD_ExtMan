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

from setuptools import setup

__version__ = "0.0.1"

setup(
    name='freecad.extman',
    version=__version__,
    packages=[
        'freecad',
        'freecad.extman',
        'freecad.extman.protocol',
        'freecad.extman.template',
        'freecad.extman.utils',
        'freecad.extman.gui',
        'freecad.extman.sources',
    ],
    maintainer="mnesarco",
    maintainer_email="mnesarco@gmail.com",
    url="https://github.com/mnesarco/FreeCAD_ExtMan",
    description="Extension Manager for FreeCAD",
    install_requires=[
        "python3-pyside2.qtwebchannel",
        "python3-pyside2.qtnetwork",
        "python3-pyside2.qtwebenginecore",
        "python3-pyside2.qtwebenginewidgets",
    ]
)
