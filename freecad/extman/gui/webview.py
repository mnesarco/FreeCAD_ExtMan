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

import json
import re
from pathlib import Path
from urllib.parse import unquote

from PySide import QtCore, QtGui
from PySide.QtCore import Qt
from PySide2 import QtWebChannel
from PySide2.QtWebEngineCore import QWebEngineUrlSchemeHandler
from PySide2.QtWebEngineWidgets import QWebEngineSettings, QWebEngineView, QWebEnginePage

from freecad.extman import log

EXTMAN_URL_SCHEME = b'extman'                               # extman://...
WINDOWS_PATH_PATTERN = re.compile(r'^/([a-zA-Z]:.*)')       # /C:... Windows insanity
ACTION_URL_PATTERN = re.compile(r'.*/action\.(\w+)$')       # action.<name>


class Response(QtCore.QObject):

    def __init__(self, parent, buffer, request):
        super().__init__(parent=parent)
        self.buffer = buffer
        self.request = request

    def write(self, data):
        self.buffer.write(data.encode())

    def send(self, content_type='text/html'):
        self.buffer.seek(0)
        self.buffer.close()
        self.request.reply(content_type.encode(), self.buffer)


class SchemeHandler(QWebEngineUrlSchemeHandler):
    """
    Process all requests with schema = extman://
    """

    def __init__(self, schemaName, requestHandler):
        super().__init__(schemaName)
        self.requestHandler = requestHandler

    def requestStarted(self, request):

        # Parse Url
        url = request.requestUrl()
        path = url.path()
        query = QtCore.QUrlQuery(url)
        params = {k: unquote(v) for k, v in query.queryItems()}

        # Fix Windows URL (This is insane)
        win_fix = WINDOWS_PATH_PATTERN.match(path)
        if win_fix:
            path = win_fix.group(1)

        # Prepare response buffer
        buf = QtCore.QBuffer(parent=self)
        request.destroyed.connect(buf.deleteLater)
        buf.open(QtCore.QIODevice.WriteOnly)

        # Match Action
        action = None
        action_match = ACTION_URL_PATTERN.match(path)
        if action_match:
            action = action_match.group(1)

        if path.endswith('.html') or action:

            # Prepare Response object
            response = Response(self, buf, request)
            request.destroyed.connect(response.deleteLater)

            # Call handler to do the real work
            # ! Important: requestHandler can work in another thread.
            # !            response.send() should be called from the handler
            # !            to send any content.
            self.requestHandler(path, action, params, request, response)

        else:

            file_path = Path(path)
            content_type = get_supported_mimetype(file_path)
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    buf.write(f.read())
                    buf.seek(0)
                    buf.close()
                    request.reply(content_type.encode(), buf)
            else:
                buf.close()
                request.reply(content_type.encode(), buf)
                log("Path does not exists: ", str(file_path))


class Page(QWebEnginePage):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def javaScriptConsoleMessage(self, *args, **kwargs):
        pass


class MessageBus(QtCore.QObject):
    """
    Manages message communication between Javascript client and Python backend
    """

    message = QtCore.Signal(str)

    def __init__(self, message_handler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message_handler = message_handler

    @QtCore.Slot(str)
    def send(self, message):
        return self.message_handler(json.loads(message))


class WebView(QtGui.QMdiSubWindow):

    closed = QtCore.Signal(object)

    def __init__(self, title, work_path, request_handler, message_handler, *args, **kwargs):
        # Window Setup
        super().__init__(*args, **kwargs)
        self.setObjectName("freecad.extman.webview")
        self.setWindowTitle(title)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # Scheme setup (extman://)
        self.handler = SchemeHandler(self, request_handler)

        # WebView setup
        self.webView = QWebEngineView(self)
        self.webView.setContextMenuPolicy(Qt.NoContextMenu)
        self.setWidget(self.webView)

        # Page setup
        self.webView.setPage(Page(self.webView))

        # Profile setup
        profile = self.webView.page().profile()
        profile.setPersistentStoragePath(str(Path(work_path, 'web_data')))
        profile.setCachePath(str(Path(work_path, 'web_cache')))
        handler = profile.urlSchemeHandler(EXTMAN_URL_SCHEME)
        if handler is not None:
            profile.removeUrlSchemeHandler(handler)
        profile.installUrlSchemeHandler(EXTMAN_URL_SCHEME, self.handler)

        # Setting setup
        settings = self.webView.settings()
        settings.setAttribute(QWebEngineSettings.AutoLoadIconsForPage, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)

        # Page settings
        page = self.webView.page().settings()
        page.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        page.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        page.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)

        # WebChannel Setup
        self.messageBus = MessageBus(message_handler, self.webView)
        self.channel = QtWebChannel.QWebChannel(self.webView)
        self.channel.registerObject('ExtManMessageBus', self.messageBus)
        self.webView.page().setWebChannel(self.channel)

    def closeEvent(self, event):
        self.closed.emit(event)
        event.accept()

    def load(self, url):
        self.webView.load(url)


def get_supported_mimetype(path):
    name = path.name.lower()
    if name.endswith('.svg'):
        content_type = 'image/svg+xml'
    elif name.endswith('.png'):
        content_type = 'image/png'
    elif name.endswith('.jpg'):
        content_type = 'image/jpeg'
    elif name.endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif name.endswith('.css'):
        content_type = 'text/css'
    elif name.endswith('.js'):
        content_type = 'text/javascript'
    else:
        content_type = 'text/plain'
    return content_type


# ! Call as soon as possible
def register_custom_schemes():
    try:
        from PySide2.QtWebEngineCore import QWebEngineUrlScheme
    except ImportError:
        log('Outdated QT version, some graphics will be not available')
    else:
        scheme_reg = QWebEngineUrlScheme(EXTMAN_URL_SCHEME)
        scheme_reg.setFlags(
            QWebEngineUrlScheme.SecureScheme
            | QWebEngineUrlScheme.LocalScheme
            | QWebEngineUrlScheme.LocalAccessAllowed
            | QWebEngineUrlScheme.ContentSecurityPolicyIgnored
            | 0x80  # QWebEngineUrlScheme.CorsEnabled
        )
        QWebEngineUrlScheme.registerScheme(scheme_reg)

