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

import os, time

import FreeCADGui as Gui
import WebGui
from PySide import QtGui, QtCore

from PySide2.QtWebEngineWidgets import QWebEngineView

from freecad.extman import tr, isWindowsPlatform, getResourcePath
from freecad.extman.html import render
from freecad.extman.worker import Worker, runInMainThread
from freecad.extman.webview import WebView, Response

_browser_instance = None                      # Singleton: WebView
_browser_session = {}                         # Singleton: State
_browser_base_path = getResourcePath('html')  # Constant:  Base dir for templates
_router = None                                # Singleton: Router configuration

def pathToExtmanUrl(path):
    if isWindowsPlatform:
        return 'extman://' + path.replace('\\', '/')
    else:
        return 'extman://' + path

class BrowserSession:

    def __init__(self, model, router):
        self.model = model
        self.model['route'] = router

    def setState(self, **kw):
        self.model.update(kw)

    def routeTo(self, route):
        self.model['route'].setRoute(route)

    def getRouter(self):
        return self.model['route']

def getUpdatedBrowserSession(**model):
    global _browser_session, _router
    if not _browser_session:
        _browser_session = BrowserSession(model, _router)
    else:
        _browser_session.setState(**model)
    return _browser_session

@QtCore.Slot(object)
def onWebViewClose(event):
    global _browser_instance
    _browser_instance = None    

def startBrowser():
    global _browser_instance
    if not _browser_instance:
        ma = Gui.getMainWindow().findChild(QtGui.QMdiArea)
        _browser_instance = WebView(tr('Extension Manager'), getResourcePath('cache'), requestHandler, ma)
        _browser_instance.closed.connect(onWebViewClose)
        ma.addSubWindow(_browser_instance)
        index = pathToExtmanUrl(getResourcePath('html', 'index.html'))
        _browser_instance.load(index)
        _browser_instance.show()
    return _browser_instance

class TemplateResponseWrapper:

    def __init__(self, response):
        self.delegate = response

    def write(self, data):
        self.delegate.write(data)

    def send(self, contentType = 'text/html'):
        self.delegate.send(contentType)

    def renderTemplate(self, template, send=True, contentType='text/html'):
        if isinstance(template, str):
            template = getResourcePath('html', template)
        else:
            template = getResourcePath('html', *template)
        html, url = render(template, model = _browser_session.model)
        self.delegate.write(html)
        if send:
            self.delegate.send(contentType)

    def render(self, content, send=True, contentType='text/html'):
        self.delegate.write(content)
        if send:
            self.delegate.send(contentType)

    def htmlOk(self):
        self.render("""
        <html>
            <head><title>Extman</title></head>
            <body>OK</body>
        </html>
        """, True)

def requestHandler(path, action, params, request, response):

    """
    Process extman:// requests
    """
    
    # Restore state
    session = getUpdatedBrowserSession()

    # Call action logic if any
    if action:
        import freecad.extman.controller as actions
        responseWrapper = TemplateResponseWrapper(response)
        eval(
            f'actions.{action}(path, session, params, request, responseWrapper)', 
            {}, 
            locals()
        )

    # Default action is render template.
    # Only templates inside html dir are allowed
    elif path.startswith(_browser_base_path):

        template = path[len(_browser_base_path)+1:]

        # Render and send
        html, url = render(template, model=session.model)
        response.write(html)
        response.send()

def installRouter(router):
    global _router
    _router = router
