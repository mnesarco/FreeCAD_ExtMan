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

import time
import random
import sys
import os
import re
import traceback
import textwrap
import contextlib
import hashlib

from io import StringIO
from urllib.parse import quote

import WebGui
import FreeCADGui as Gui

from PySide import QtGui
from freecad.extman import tr, getResourcePath, isWindowsPlatform, log
from freecad.extman.html_components import components
from freecad.extman.html_utils import getResourceUrl
from freecad.extman.html_cache import useCacheArea

# ${t:text}                          => Translate text
# ${e:expression}                    => eval expression
# ${x:statememt}                     => exec statement
# ${e:include(*template, **params)}  => inckude template with params
TEMPLATE_EXPR_PATTERN = re.compile(r'\${([tex]:)?\s*([^}]+)}', flags=re.S)
TEMPLATE_EXEC_PATTERN = re.compile(r'<py>(.*?)</py>', flags=re.S)
TEMPLATE_MACRO_PATTERN = re.compile(r'@{macro:\s*(\w+)\b[^}]*}(.*?)@{/macro}', flags=re.S)

def sha256(input):
    return hashlib.sha256(input.encode()).hexdigest()

class DictObject:
    
    def __init__(self, data, errorOnMissing=False):
        self.errorOnMissing = errorOnMissing
        self.__dict__ = data

    def __getattr__(self, name):
        if self.errorOnMissing:
            raise AttributeError('{0} not defined'.format(name))
        else:
            return None

def TemplateMacro(name, code, path):

    """
    Main Template Engine Macro Builder
    """

    def macroDef(model):
        def macroImpl(**args):
            scope = dict(model)
            scope.update(args)
            evaluator = TemplateExpressionEvaluator(path, scope)
            return TEMPLATE_EXPR_PATTERN.sub(evaluator, code)
        return macroImpl
    return macroDef

class HtmlPrint:
    
    def __init__(self):
        self.out = StringIO()

    def __call__(self, *args):
        result = "".join((str(arg) for arg in args))
        self.out.write(result)

    def getOutput(self):
        output = self.out.getvalue()
        self.out.close()
        del self.out
        return output

def TemplateExpressionEvaluator(path, model):

    """
    Main Template Engine Evaluator
    """

    def compileAndExecute(eexpr, model, mode = 'eval'):
        if mode == 'eval':
            output = eval(eexpr, {}, model)
            return output if output else ''
        else:
            compiled = compile(eexpr, '<string>', mode)
            savedPrint = model.get('hprint')
            printStream = HtmlPrint()
            try:
                model['hprint'] = printStream
                exec(compiled, {}, model)
            finally:
                model['hprint'] = savedPrint
            output = printStream.getOutput()
            return output if output else ''

    def evalExpr(match):
        try:
            etype  = match.group(1)
            eexpr  = match.group(2)
            # Transale shortcut
            if etype == 't:':
                return tr(eexpr)
            # Eval Expression
            elif etype == 'e:':
                return compileAndExecute(eexpr, model, 'eval')
            # Execute Statement
            elif etype == 'x:':
                return compileAndExecute(eexpr, model, 'exec')
            # Resolve local symbol
            else:
                return str(model.get(eexpr, '???{0}{1}???'.format(etype, eexpr)))
        except:
            log(traceback.format_exc())
            log("Error executing expression {0} in template {1}".format(eexpr, path))
            return 'Error:' + traceback.format_exc()
            
    return evalExpr

def TemplateMapper(*basePath, model=None):

    """
    Main Template Engine Mapper (includer)
    """

    basePath = basePath[:-1]
    def mapTemplate(*path, **params):
        subPath = basePath + path
        url, context, absPath = getResourceUrl(*subPath)
        scope = dict(model or {})
        scope.update({'params': DictObject(params)})
        return processTemplate(absPath, scope)
    return mapTemplate

def processTemplate(path, model):

    """
    Load template from path and evaluate it
    """

    (html, macros) = getTemplate(path)
    scope = dict(model or {})
    for name, builder in macros.items():
        scope[name] = builder(scope) 

    evaluator = TemplateExpressionEvaluator(path, scope)
    return TEMPLATE_EXPR_PATTERN.sub(evaluator, html)

def parseMacros(code, path):

    """
    Main Template Engine: Parse macros into callable functions
    """

    macros = {}
    def saveMacro(match):
        name = match.group(1)
        code = match.group(2)
        macros[name] = TemplateMacro(name, code, path)
        return ""
    parsed = TEMPLATE_MACRO_PATTERN.sub(saveMacro, code)
    return (parsed, macros)

def parseBlocks(code, path):

    """
    Main Template Engine: Parse python blocks into callable functions
    """
    blocks = {}
    def compileBlock(match):
        block = textwrap.dedent(match.group(1))
        name = "block_{0}_{1}".format(random.randint(0, 65000), int(time.time()))
        blocks[name] = TemplateMacro(name, block, path)
        return '${x:' + block + '()}'

    parsed = TEMPLATE_EXEC_PATTERN.sub(compileBlock, code)
    return (parsed, blocks)

def getTemplate(path):

    """
    Main Template Engine Parser
    """

    with open(path) as f:
        # Read all templace code
        code = f.read()
        # Compile all blocks
        code, blocks = parseBlocks(code, path)
        # Parse all macros
        code, macros = parseMacros(code, path)
        # Merge macros ad blocks
        macros.update(blocks)
        return (code, macros)

def render(*path, model):

    """
    Main Template Engine Renderer
    """

    url, context, absPath = getResourceUrl(*path)
    model['_URL_'] = url
    model['_BASE_'] = context
    model['_FILE_'] = absPath
    model['include'] = TemplateMapper(absPath, model=model)
    model['tr'] = tr
    model['comp'] = components
    model['urlencode'] = quote
    model['sha256'] = sha256
    return processTemplate(absPath, model=model), url

