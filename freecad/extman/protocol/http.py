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

import FreeCAD as App
import sys
import traceback
import urllib.error as errors
import urllib.request as request

from freecad.extman import log

# <Start Legacy urllib code>
#   Can be replaced by modern request lib but
#   I leave it with urllib to avoid dependency problems
ssl_ctx = None
request_initialized = False

try:
    import ssl
except ImportError:
    pass
else:
    try:
        ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    except AttributeError:
        pass


def get_proxy_conf():
    pref = App.ParamGet("User parameter:BaseApp/Preferences/Addons")
    if pref.GetBool("NoProxyCheck", True):
        proxies = {}
    else:
        if pref.GetBool("SystemProxyCheck", False):
            proxy = request.getproxies()
            proxies = {"http": proxy.get('http'), "https": proxy.get('http')}
        elif pref.GetBool("UserProxyCheck", False):
            proxy = pref.GetString("ProxyUrl", "")
            proxies = {"http": proxy, "https": proxy}
    return request.ProxyHandler(proxies)


def get_ssh_handler():
    if ssl_ctx:
        return request.HTTPSHandler(context=ssl_ctx)
    else:
        return {}


def urllib_init():
    global request_initialized
    if not request_initialized:
        proxy_support = get_proxy_conf()
        handler = get_ssh_handler()
        opener = request.build_opener(proxy_support, handler)
        request.install_opener(opener)
        request_initialized = True


# <End Legacy urllib code>

def http_get(url, headers=None, timeout=30, decode='utf-8'):
    urllib_init()
    data = None
    try:
        with request.urlopen(request.Request(url, headers=headers or {}), timeout=timeout) as f:
            block = 8192
            if decode:
                data = ''
            else:
                data = []
            while True:
                p = f.read(block)
                if not p:
                    break
                if isinstance(p, bytes) and decode:
                    p = p.decode(decode)
                data += p
    except errors.URLError as ex:
        log(url, str(ex.reason))
    except:
        log(traceback.format_exc())

    return data


def http_download(url, path, headers=None, timeout=30):
    urllib_init()
    try:
        with request.urlopen(request.Request(url, headers=headers or {}), timeout=timeout) as stream:
            with open(path, 'wb') as localFile:
                block = 8192
                while True:
                    p = stream.read(block)
                    if not p: break
                    localFile.write(p)
                return True
    except errors.URLError as ex:
        log(url, str(ex.reason))
    except:
        log(traceback.format_exc())

    return False
