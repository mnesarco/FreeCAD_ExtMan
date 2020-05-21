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

import re
import tempfile
import os
import FreeCAD as App
import FreeCADGui as Gui
import hashlib

from PySide import QtGui, QtCore
from freecad.extman import getResourcePath, isWindowsPlatform, tr

thumbnailsDir = tempfile.mkdtemp(prefix="xpm_thumbnails")
xmpCache = {}

COMMA_SEP_LIST_PATTERN = re.compile(r'\s*,\s*', re.S)

STRIP_TAGS_PATTERN = re.compile(r'<[^>]+>|<!--.*', re.S)

ABS_PATH_PATTERN = re.compile(r'^(\s|/|\\)*(?P<rel>.*)')

WORKBENCH_CLASS_NAME_PATTERN = re.compile(r'addWorkbench\s*\(\s*(?P<class>\w+)')

#!-----------------------------------------------------------------------------
#! Fix windows Crap
#! symlinks support
if isWindowsPlatform:
    wsl = getattr(os, 'symlink', None)
    if not callable(wsl):
        #! See: https://stackoverflow.com/a/28382515/1524027
        def symlink_ms(source, link_name):
            import ctypes # Import here as a special case for windows only
            csl = ctypes.windll.kernel32.CreateSymbolicLinkW
            csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
            csl.restype = ctypes.c_ubyte
            flags = 1 if os.path.isdir(source) else 0
            try:
                if csl(link_name, source.replace('/', '\\'), flags) == 0:
                    raise ctypes.WinError()
            except:
                pass
        os.symlink = symlink_ms

nonStandardNamedWorkbenches = {
    "flamingo"        : "flamingoToolsWorkbench",
    "geodata"         : "GeodatWorkbench",
    "A2plus"          : "a2pWorkbench",
    "ArchTextures"    : "ArchTextureWorkbench",
    "cadquery_module" : "CadQueryWorkbench",
    "Defeaturing"     : "DefeaturingWB",
    "kicadStepUpMod"  : "KiCadStepUpWB",
    "Manipulator"     : "ManipulatorWB",
    "Part-o-magic"    : "PartOMagicWorkbench",
    "sheetmetal"      : "SMWorkbench",
    "FCGear"          : "gearWorkbench",
    "frame"           : "frame_Workbench",
    'CurvedShapes'    : "CurvedShapesWB",
    "None"            : None
}

predefinedCategories = {
    "ArchWorkbench" : [tr("Architecture")],
    "CompleteWorkbench" : [tr("Other")],
    "DraftWorkbench" : [tr("CAD/CAM")],
    "DrawingWorkbench" : [tr("CAD/CAM")],
    "FemWorkbench" : [tr("Analysis")],
    "ImageWorkbench" : [tr("Other")],
    "InspectionWorkbench" : [tr("Analysis")],
    "MeshWorkbench" : [tr("3D")],
    "OpenSCADWorkbench" : [tr("CAD/CAM")],
    "PartWorkbench" : [tr("CAD/CAM")],
    "PartDesignWorkbench" : [tr("CAD/CAM")],
    "PathWorkbench" : [tr("CAD/CAM")],
    "PointsWorkbench" : [tr("CAD/CAM")],
    "RaytracingWorkbench" : [tr("3D")],
    "ReverseEngineeringWorkbench" : [tr("Engineering")],
    "RobotWorkbench" : [tr("Engineering")],
    "SketcherWorkbench" : [tr("CAD/CAM")],
    "SpreadsheetWorkbench" : [tr("Data")],
    "StartWorkbench" : [tr("Other")],
    "TechDrawWorkbench" : [tr("CAD/CAM")],
    "TestWorkbench" : [tr("Other")],
    "WebWorkbench" : [tr("Other")],
    "gearWorkbench" : [tr("Engineering")],
    "CurvesWorkbench" : [tr("CAD/CAM")],
    "CurvedShapesWB" : [tr("CAD/CAM")],
    "ExtManWorkbench" : [tr("Other")],
    "KiCadStepUpWB" : [tr("PCB/EDA")]
}

def pathToUrl(path):

    if path.startswith('file://'):
        return path

    if isWindowsPlatform:
        path = path.replace('\\', '/')

    return 'file://' + path

def extractIcon(src, default='freecad.svg'):
    if "XPM" in src:
        try:
            xmphash = hashlib.sha256(src.encode()).hexdigest()
            if xmphash in xmpCache:
                return xmpCache[xmphash]
            xpm = xpm.replace("\n        ","\n")
            r = [s[:-1].strip('"') for s in re.findall("(?s)\{(.*?)\};",xpm)[0].split("\n")[1:]]
            p = QtGui.QPixmap(r)
            p = p.scaled(24,24)
            img = tempfile.mkstemp(dir = thumbnailsDir, suffix = '.png')[1]
            p.save(img)
            xmpCache[xmphash] = img
            return img
        except:
            return getResourcePath('html', 'img', default)
    else:
        try:
            if os.path.exists(src):
                return src
            else:
                return getResourcePath('html', 'img', default)
        except:
            return src

def getWorkbenchKey(name):
    if name.endswith("Workbench"): name = name[:-9]
    return nonStandardNamedWorkbenches.get(name, "{0}Workbench".format(name))

def getWorkbenchCategories(wb):
    if wb and hasattr(wb, 'Categories'):
        return wb.Categories
    else:
        return predefinedCategories.get(wb.__class__.__name__, [tr('Uncategorized')])

def getWorkbenchCategoriesFromString(name, cats):
    if cats:
        if isinstance(cats, str):
            return [ tr(c) for c in CommaStringList(cats) ]
        elif isinstance(cats, list):
            return [ tr(c) for c in cats ]    
    
    return predefinedCategories.get(name, [tr('Uncategorized')])

_CORE_RES_DIR_   = '_CORE_RES_DIR_'
_CORE_RES_URL_   = '_CORE_RES_URL_'

_USER_DATA_DIR_  = '_USER_DATA_DIR_'
_USER_DATA_URL_  = '_USER_DATA_URL_'

_USER_MACRO_DIR_ = '_USER_MACRO_DIR_'
_USER_MACRO_URL_ = '_USER_MACRO_URL_'

#! I don't like this code, improve later
# This is used to store data in files as cache without hard references to
# FreeCAD directories because directories can be different at restore time
# ie. AppImage
def removeAbsolutePaths(content):
    """Replace absolute paths to placeholders."""

    coreResDir = App.getResourceDir()
    content = content.replace(pathToUrl(coreResDir), _CORE_RES_URL_)
    content = content.replace(coreResDir, _CORE_RES_DIR_)

    userDataDir = App.getUserAppDataDir()
    if (userDataDir):
        content = content.replace(pathToUrl(userDataDir), _USER_DATA_URL_)
        content = content.replace(userDataDir, _USER_DATA_DIR_)

    userMacroDir = App.getUserMacroDir(True)
    if (userMacroDir):
        content = content.replace(pathToUrl(userMacroDir), _USER_MACRO_URL_)
        content = content.replace(userMacroDir, _USER_MACRO_DIR_)

    return content

#! See: removeAbsolutePaths
def restoreAbsolutePaths(content):
    
    """Replace placeholders with current absolute paths."""

    coreResDir = App.getResourceDir()
    content = content.replace(_CORE_RES_DIR_, coreResDir)
    content = content.replace(_CORE_RES_URL_, pathToUrl(coreResDir))

    userDataDir = App.getUserAppDataDir()
    content = content.replace(_USER_DATA_DIR_, userDataDir)
    content = content.replace(_USER_DATA_URL_, pathToUrl(userDataDir))

    userMacroDir = App.getUserMacroDir(True)
    content = content.replace(_USER_MACRO_DIR_, userMacroDir)
    content = content.replace(_USER_MACRO_URL_, pathToUrl(userMacroDir))

    return content

def getWorkbenchIconCandidates(workbenchName, baseUrl, iconPath, localDir, cacheDir):
    # Legacy icon compiled inside FreeCAD
    sources = ["qrc:/icons/" + workbenchName + "_workbench_icon.svg"]
    if iconPath:
        # Locally installed icon
        sources.append('file://' + os.path.join(localDir, iconPath)) 
        # Locally cached icon
        sources.append('file://' + os.path.join(cacheDir, workbenchName + "_workbench_icon.svg"))
        # Remote icon
        if baseUrl.endswith('.git'):
            baseUrl = baseUrl[:-4]
        if baseUrl.endswith('/'):
            baseUrl = baseUrl[:-1]
        sources.append(baseUrl + '/' + iconPath)
    return sources

def CommaStringList(content):
    return COMMA_SEP_LIST_PATTERN.split(content)

def SanitizedHtml(html):
    if html:
        return STRIP_TAGS_PATTERN.sub('', html)

def symlink(source, link):
    if os.path.exists(source):
        if not (os.path.exists(link) or os.path.lexists(link)):
            os.symlink(source, link)

def pathRel(path):
    m = ABS_PATH_PATTERN.match(path)
    if m:
        return m.group('rel').replace('/', os.path.sep)
    else:
        return None

def restartFreeCAD():
    args = QtGui.QApplication.arguments()[1:]
    if Gui.getMainWindow().close():
        QtCore.QProcess.startDetached(QtGui.QApplication.applicationFilePath(), args)

def extractWorkbenchClassName(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        m = WORKBENCH_CLASS_NAME_PATTERN.search(content)
        if m:
            return m.group('class')

def analyseInstalledWorkbench(pkg):
    
    # Check Legacy InitGui.py
    init = os.path.join(pkg.installDir, 'InitGui.py')
    if os.path.exists(init):
        key = extractWorkbenchClassName(init)
        if key:
            pkg.key = key
            return
    
    # Check init_gui.py
    fcp = os.path.join(pkg.installDir, 'freecad')
    if os.path.exists(fcp) and os.path.isdir(fcp):
        for subp in os.listdir(fcp):
            path = os.path.join(fcp, subp)
            if os.path.isdir(path):
                init = os.path.join(path, 'init_gui.py')
                if os.path.exists(init):
                    key = extractWorkbenchClassName(init)
                    if key:
                        pkg.key = key
                        return
