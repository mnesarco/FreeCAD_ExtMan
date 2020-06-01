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

import FreeCADGui as Gui
import hashlib
import re
from PySide import QtGui, QtCore
from pathlib import Path

from freecad.extman import (tr, get_freecad_resource_path, get_macro_path,
                            get_app_data_path, get_resource_path, get_cache_path)

from freecad.extman.protocol.manifest import ExtensionManifest
from freecad.extman.sources import PackageInfo

XPM_CACHE = {}

COMMA_SEP_LIST_PATTERN = re.compile(r'\s*,\s*', re.S)

STRIP_TAGS_PATTERN = re.compile(r'<[^>]+>|<!--.*', re.S)

ABS_PATH_PATTERN = re.compile(r'^(\s|/|\\)*(?P<rel>.*)')

WORKBENCH_CLASS_NAME_PATTERN = re.compile(r'addWorkbench\s*\(\s*(?P<class>\w+)')

_CORE_RES_DIR_ = '_CORE_RES_DIR_'
_CORE_RES_URL_ = '_CORE_RES_URL_'

_USER_DATA_DIR_ = '_USER_DATA_DIR_'
_USER_DATA_URL_ = '_USER_DATA_URL_'

_USER_MACRO_DIR_ = '_USER_MACRO_DIR_'
_USER_MACRO_URL_ = '_USER_MACRO_URL_'

nonStandardNamedWorkbenches = {
    "flamingo": "flamingoToolsWorkbench",
    "geodata": "GeodatWorkbench",
    "A2plus": "a2pWorkbench",
    "ArchTextures": "ArchTextureWorkbench",
    "cadquery_module": "CadQueryWorkbench",
    "Defeaturing": "DefeaturingWB",
    "kicadStepUpMod": "KiCadStepUpWB",
    "Manipulator": "ManipulatorWB",
    "Part-o-magic": "PartOMagicWorkbench",
    "sheetmetal": "SMWorkbench",
    "FCGear": "gearWorkbench",
    "frame": "frame_Workbench",
    'CurvedShapes': "CurvedShapesWB",
    "None": None
}

predefinedCategories = {
    "ArchWorkbench": [tr("Architecture")],
    "CompleteWorkbench": [tr("Other")],
    "DraftWorkbench": [tr("CAD/CAM")],
    "DrawingWorkbench": [tr("CAD/CAM")],
    "FemWorkbench": [tr("Analysis")],
    "ImageWorkbench": [tr("Other")],
    "InspectionWorkbench": [tr("Analysis")],
    "MeshWorkbench": [tr("3D")],
    "OpenSCADWorkbench": [tr("CAD/CAM")],
    "PartWorkbench": [tr("CAD/CAM")],
    "PartDesignWorkbench": [tr("CAD/CAM")],
    "PathWorkbench": [tr("CAD/CAM")],
    "PointsWorkbench": [tr("CAD/CAM")],
    "RaytracingWorkbench": [tr("3D")],
    "ReverseEngineeringWorkbench": [tr("Engineering")],
    "RobotWorkbench": [tr("Engineering")],
    "SketcherWorkbench": [tr("CAD/CAM")],
    "SpreadsheetWorkbench": [tr("Data")],
    "StartWorkbench": [tr("Other")],
    "TechDrawWorkbench": [tr("CAD/CAM")],
    "TestWorkbench": [tr("Other")],
    "WebWorkbench": [tr("Other")],
    "gearWorkbench": [tr("Engineering")],
    "CurvesWorkbench": [tr("CAD/CAM")],
    "CurvedShapesWB": [tr("CAD/CAM")],
    "ExtManWorkbench": [tr("Other")],
    "KiCadStepUpWB": [tr("PCB/EDA")]
}


def path_to_url(path):
    return Path(path).as_uri().replace('file:', 'extman:')


def extract_icon(src, default='freecad.svg'):

    default_path = get_resource_path('html', 'img', default)
    xpm_path = Path(get_cache_path(), 'xpm')
    if not xpm_path.exists():
        xpm_path.mkdir(parents=True)

    if "XPM" in src:
        try:
            xpm_hash = hashlib.sha256(src.encode()).hexdigest()
            if xpm_hash in XPM_CACHE:
                return XPM_CACHE[xpm_hash]
            xpm = src.replace("\n        ", "\n")
            r = [s[:-1].strip('"') for s in re.findall(r"(?s)\{(.*?)\};", xpm)[0].split("\n")[1:]]
            p = QtGui.QPixmap(r)
            p = p.scaled(24, 24)
            img = Path(xpm_path, xpm_hash + '.png')
            p.save(img)
            if img.exists():
                XPM_CACHE[xpm_hash] = str(img)
                return str(img)
            else:
                return default_path
        except:
            return default_path
    else:
        try:
            if Path(src).exists():
                return src
            else:
                return default_path
        except:
            return src


def get_workbench_key(name):
    if name.endswith("Workbench"):
        name = name[:-9]
    return nonStandardNamedWorkbenches.get(name, "{0}Workbench".format(name))


def get_workbench_categories(wb):
    if wb and hasattr(wb, 'Categories'):
        return wb.Categories
    else:
        return predefinedCategories.get(wb.__class__.__name__, [tr('Uncategorized')])


def get_workbench_categories_from_string(name, cats):
    if cats:
        if isinstance(cats, str):
            return [tr(c) for c in CommaStringList(cats)]
        elif isinstance(cats, list):
            return [tr(c) for c in cats]

    return predefinedCategories.get(name, [tr('Uncategorized')])


def remove_absolute_paths(content):
    """Replace absolute paths to placeholders."""

    # ! I don't like this code, improve later
    # This is used to store data in files as cache without hard references to
    # FreeCAD directories because directories can be different at restore time
    # ie. AppImage

    core_res_dir = get_freecad_resource_path()
    content = content.replace(core_res_dir.as_uri(), _CORE_RES_URL_)
    content = content.replace(str(core_res_dir), _CORE_RES_DIR_)

    user_data_dir = get_app_data_path()
    content = content.replace(user_data_dir.as_uri(), _USER_DATA_URL_)
    content = content.replace(str(user_data_dir), _USER_DATA_DIR_)

    user_macro_dir = get_macro_path()
    content = content.replace(user_macro_dir.as_uri(), _USER_MACRO_URL_)
    content = content.replace(str(user_macro_dir), _USER_MACRO_DIR_)

    return content


def restore_absolute_paths(content):
    """Replace placeholders with current absolute paths."""

    core_res_dir = get_freecad_resource_path()
    content = content.replace(_CORE_RES_DIR_, str(core_res_dir))
    content = content.replace(_CORE_RES_URL_, core_res_dir.as_uri())

    user_data_dir = get_app_data_path()
    content = content.replace(_USER_DATA_DIR_, str(user_data_dir))
    content = content.replace(_USER_DATA_URL_, user_data_dir.as_uri())

    user_macro_dir = get_macro_path()
    content = content.replace(_USER_MACRO_DIR_, str(user_macro_dir))
    content = content.replace(_USER_MACRO_URL_, user_macro_dir.as_uri())

    return content


def get_workbench_icon_candidates(workbench_name, base_url, icon_path, local_dir):

    # Legacy icon compiled inside FreeCAD
    sources = ["qrc:/icons/" + workbench_name + "_workbench_icon.svg"]

    # Icon from metadata
    if icon_path:
        if icon_path.startswith('http'):
            sources.append(icon_path)
        elif icon_path.startswith('Resources'):
            src = Path(local_dir, icon_path)
            if src.exists():
                sources.append(src.as_uri().replace('file:', 'extman:'))
            else:
                sources.append(base_url.strip('/') + '/' + icon_path)
        elif icon_path.startswith('file:'):
            sources.append(icon_path.replace('file:', 'extman:'))
        elif icon_path.startswith('extman:'):
            sources.append(icon_path)

    return sources


def CommaStringList(content):
    return COMMA_SEP_LIST_PATTERN.split(content)


def SanitizedHtml(html):
    if html:
        return STRIP_TAGS_PATTERN.sub('', html)


def path_relative(path):
    m = ABS_PATH_PATTERN.match(path)
    if m:
        return m.group('rel').replace('\\', '/')
    else:
        return None


def restart_freecad():
    args = QtGui.QApplication.arguments()[1:]
    if Gui.getMainWindow().close():
        QtCore.QProcess.startDetached(QtGui.QApplication.applicationFilePath(), args)


def extract_workbench_class_name(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        m = WORKBENCH_CLASS_NAME_PATTERN.search(content)
        if m:
            return m.group('class')


def analyse_installed_workbench(pkg):

    # Read Manifest
    manifest_file = Path(pkg.installDir, 'manifest.ini')
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest_content = f.read()
            manifest = ExtensionManifest(manifest_content)
            if isinstance(pkg, PackageInfo):
                manifest.getData(pkg.__dict__)
            elif isinstance(pkg, dict):
                manifest.getData(pkg)

    # Check Legacy InitGui.py
    init = Path(pkg.installDir, 'InitGui.py')
    if init.exists():
        key = extract_workbench_class_name(init)
        if key:
            pkg.key = key
            return

    # Check init_gui.py
    fcp = Path(pkg.installDir, 'freecad')
    if fcp.is_dir():
        for path in fcp.iterdir():
            if path.is_dir():
                init = Path(path, 'init_gui.py')
                if init.exists():
                    key = extract_workbench_class_name(init)
                    if key:
                        pkg.key = key
                        return

