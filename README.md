# FreeCAD Extension Manager

## Description

This project is an attempt to improve management of FreeCAD Extensions repositories. The current solution is the built-in FreeCAD [Addon Manager](https://wiki.freecadweb.org/AddonManager). Eventually this project aims to replace it.

## Install

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


![Menu](https://github.com/mnesarco/FreeCAD_ExtMan/blob/master/freecad/extman/resources/docs/workbenches.png)


| :warning: WARNING: This project is in active development and it is not ready for final users. |
| --- |

## Features

* Improved UI/UX
* Extension Manager will pull submodules for repos that use them, automatically

## Python Requirements

* python3-pyside2.qtwebchannel
* python3-pyside2.qtnetwork
* python3-pyside2.qtwebenginecore
* python3-pyside2.qtwebenginewidgets

## Core Classes

![Classes](https://github.com/mnesarco/FreeCAD_ExtMan/blob/master/freecad/extman/resources/docs/core-classes.png)

## UI Rendering

![Sequence](https://github.com/mnesarco/FreeCAD_ExtMan/blob/master/freecad/extman/resources/docs/gui-cycle.png)
