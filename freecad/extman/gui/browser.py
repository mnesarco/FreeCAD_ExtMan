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
from PySide import QtGui, QtCore

from freecad.extman.gui.controller import actions, message_handlers
from freecad.extman import tr, get_resource_path, get_cache_path, log, log_err
from freecad.extman.template.html import render
from freecad.extman.gui.webview import WebView

__browser_instance__ = None                         # Singleton: WebView
__browser_session__ = {}                            # Singleton: State
__browser_base_path__ = get_resource_path('html')   # Constant:  Base dir for templates
__router__ = None                                   # Singleton: Router configuration


def path_to_extman_url(path):
    return path.as_uri().replace('file:', 'extman:')


class BrowserSession:

    def __init__(self, model, router):
        self.model = model
        self.model['route'] = router

    def set_state(self, **kw):
        self.model.update(kw)

    def route_to(self, route):
        self.model['route'].set_route(route)

    def get_router(self):
        return self.model['route']


def get_updated_browser_session(**model):
    global __browser_session__, __router__
    if not __browser_session__:
        __browser_session__ = BrowserSession(model, __router__)
    else:
        __browser_session__.set_state(**model)
    return __browser_session__


@QtCore.Slot(object)
def on_web_view_close(event):
    global __browser_instance__
    __browser_instance__ = None


def start_browser():
    global __browser_instance__
    if not __browser_instance__:
        main_window = Gui.getMainWindow().findChild(QtGui.QMdiArea)
        bi = WebView(
            tr('Extension Manager'),
            get_cache_path(),
            request_handler,
            message_handler,
            main_window)
        bi.closed.connect(on_web_view_close)
        main_window.addSubWindow(bi)
        index = path_to_extman_url(get_resource_path('html', 'index.html'))
        bi.load(index)
        bi.show()
        __browser_instance__ = bi
    return __browser_instance__


class TemplateResponseWrapper:

    def __init__(self, response):
        self.delegate = response

    def write(self, data):
        self.delegate.write(data)

    def send(self, content_type='text/html'):
        self.delegate.send(content_type)

    def render_template(self, template, send=True, content_type='text/html'):
        if isinstance(template, str):
            template = get_resource_path('html', template)
        else:
            template = get_resource_path('html', *template)
        html, url = render(template, model=__browser_session__.model)
        self.delegate.write(html)
        if send:
            self.delegate.send(content_type)

    def render(self, content, send=True, content_type='text/html'):
        self.delegate.write(content)
        if send:
            self.delegate.send(content_type)

    def html_ok(self):
        self.render("""
        <html>
            <head><title>Extman</title></head>
            <body>OK</body>
        </html>
        """, True)


def request_handler(path, action, params, request, response):
    """
    Process extman:// requests from webview
    """

    # Restore state
    session = get_updated_browser_session()

    # Call action logic if any
    if action:
        response_wrapper = TemplateResponseWrapper(response)
        try:
            handler = actions[action]
        except KeyError:
            log_err("Invalid action {0}".format(action))
        else:
            handler(path, session, params, request, response_wrapper)

    # Default action is render template.
    else:
        html, url = render(path, model=session.model)
        response.write(html)
        response.send()


def message_handler(message):
    """
    Process Javascript messages from webview
    """

    try:
        handler_name = message['handler']
    except KeyError:
        log_err("Invalid handler {0}".format(handler_name))
    else:
        try:
            handler = message_handlers[handler_name]
        except KeyError:
            log_err("Invalid handler {0}".format(handler_name))
        else:
            handler(message, get_updated_browser_session())


def install_router(router):
    global __router__
    __router__ = router
