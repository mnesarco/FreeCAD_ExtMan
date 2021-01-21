# FreeCAD Extension Manager (For FreeCAD 0.19+)

## Description

This project is an attempt to improve management of FreeCAD Extensions repositories. The current solution is the built-in FreeCAD [Addon Manager](https://wiki.freecadweb.org/AddonManager). Eventually this project aims to replace it.

![Sequence](https://github.com/mnesarco/FreeCAD_ExtMan/raw/master/freecad/extman/resources/docs/ExtMan_Screenshot1.png)

Old video: https://www.youtube.com/watch?v=PNQObE37vxE

## Install

### Dependencies

If you are using the AppImage, everything is already included, but if you are using a system installed version, or a locally compiled version, you must install the python dependencies listed here:

```
python3-pyside2.qtwebchannel
python3-pyside2.qtnetwork
python3-pyside2.qtwebenginecore
python3-pyside2.qtwebenginewidgets
```

### Git
```
cd ~/.FreeCAD/Mod
git clone https://github.com/mnesarco/FreeCAD_ExtMan.git ExtMan
```
Restart FreeCAD

### Zip
```
cd ~/.FreeCAD/Mod
curl -LOk https://github.com/mnesarco/FreeCAD_ExtMan/archive/master.zip
unzip master.zip
mv FreeCAD_ExtMan-master ExtMan
```
Restart FreeCAD

### Usage

Once installed, restart FreeCAD and activate it from the Workbenches list.


![Menu](https://github.com/mnesarco/FreeCAD_ExtMan/raw/master/freecad/extman/resources/docs/workbenches.png)


## Features

* Improved UI/UX
* Extension Manager will pull submodules for repos that use them, automatically

## Python Requirements

* python3-pyside2.qtwebchannel
* python3-pyside2.qtnetwork
* python3-pyside2.qtwebenginecore
* python3-pyside2.qtwebenginewidgets



# Technical Info for developers

## Core Classes

![Classes](https://github.com/mnesarco/FreeCAD_ExtMan/raw/master/freecad/extman/resources/docs/core-classes.png)

## UI Rendering

![Sequence](https://github.com/mnesarco/FreeCAD_ExtMan/raw/master/freecad/extman/resources/docs/gui-cycle.png)
