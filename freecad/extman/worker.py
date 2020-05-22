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

import sys
import traceback
from PySide import QtCore as qt


class InvokeEvent(qt.QEvent):
    EVENT_TYPE = qt.QEvent.Type(qt.QEvent.registerEventType())

    def __init__(self, fn, *args, **kwargs):
        qt.QEvent.__init__(self, InvokeEvent.EVENT_TYPE)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class Invoker(qt.QObject):

    def event(self, event):
        event.fn(*event.args, **event.kwargs)
        return True


def run_in_main_thread(fn, *args, **kwargs):
    qt.QCoreApplication.postEvent(
        UIThreadInvoker,
        InvokeEvent(fn, *args, **kwargs)
    )


class WorkerSignals(qt.QObject):
    started = qt.Signal(tuple)
    finished = qt.Signal(tuple)


class Worker(qt.QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.signals = WorkerSignals()
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.error = None
        self.isRunning = False
        self.isPending = True
        self._cancel = False
        self.fn = fn

    def run(self):
        self.isPending = False
        if not self._cancel:
            try:
                self.isRunning = True
                self.signals.started.emit((self,))
                self.result = self.fn(*self.args, **self.kwargs)
            except BaseException as ex:
                self.error = ex
                traceback.print_exc(file=sys.stderr)
            except Exception as ex:
                self.error = ex
                traceback.print_exc(file=sys.stderr)
            except:  # Catch everything else
                self.error = BaseException(traceback.format_exc())
                traceback.print_exc(file=sys.stderr)
            finally:
                self.isRunning = False
                self.signals.finished.emit((self.result, self.error, self))

    def start(self):
        qt.QThreadPool.globalInstance().start(self)

    def cancel(self):
        if self.isPending:
            self._cancel = True
            return True
        return False

    def get(self):

        while self.isPending:
            if self._cancel:
                return None

        while True:
            if not self.isRunning:
                if self.error:
                    raise self.error
                else:
                    return self.result


UIThreadInvoker = Invoker()
