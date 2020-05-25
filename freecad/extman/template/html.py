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

import hashlib
import random
import re
import textwrap
import time
import traceback
from io import StringIO
from urllib.parse import quote

from freecad.extman import tr, log
from freecad.extman.template.html_components import components
from freecad.extman.template.html_utils import get_resource_url

# ${t:text}                          => Translate text
# ${e:expression}                    => eval expression
# ${x:statement}                     => exec statement
# ${e:include(*template, **params)}  => include template with params
TEMPLATE_EXPR_PATTERN = re.compile(r'\${([tex]:)?\s*([^}]+)}', flags=re.S)
TEMPLATE_EXEC_PATTERN = re.compile(r'<py>(.*?)</py>', flags=re.S)
TEMPLATE_MACRO_PATTERN = re.compile(r'@{macro:\s*(\w+)\b[^}]*}(.*?)@{/macro}', flags=re.S)


def sha256(input):
    return hashlib.sha256(input.encode()).hexdigest()


class DictObject:

    def __init__(self, data, error_on_missing=False):
        self.errorOnMissing = error_on_missing
        self.__dict__ = data

    def __getattr__(self, name):
        if self.errorOnMissing:
            raise AttributeError('{0} not defined'.format(name))
        else:
            return None


def template_macro(name, code, path):
    """
    Main Template Engine Macro Builder
    """

    def macro_def(model):
        def macro_impl(**args):
            scope = dict(model)
            scope.update(args)
            evaluator = template_expression_evaluator(path, scope)
            return TEMPLATE_EXPR_PATTERN.sub(evaluator, code)

        return macro_impl

    return macro_def


class HtmlPrint:

    def __init__(self):
        self.out = StringIO()

    def __call__(self, *args):
        result = "".join((str(arg) for arg in args))
        self.out.write(result)

    def get_output(self):
        output = self.out.getvalue()
        self.out.close()
        del self.out
        return output


def template_expression_evaluator(path, model):
    """
    Main Template Engine Evaluator
    """

    def compile_and_execute(eexpr, emodel, mode='eval'):
        if mode == 'eval':
            output = eval(eexpr, {}, emodel)
            return output if output else ''
        else:
            compiled = compile(eexpr, '<string>', mode)
            saved_print = emodel.get('hprint')
            print_stream = HtmlPrint()
            try:
                emodel['hprint'] = print_stream
                exec(compiled, {}, emodel)
            finally:
                emodel['hprint'] = saved_print
            output = print_stream.get_output()
            return output if output else ''

    def eval_expr(match):
        try:
            etype = match.group(1)
            eexpr = match.group(2)
            # Translate shortcut
            if etype == 't:':
                return tr(eexpr)
            # Eval Expression
            elif etype == 'e:':
                return compile_and_execute(eexpr, model, 'eval')
            # Execute Statement
            elif etype == 'x:':
                return compile_and_execute(eexpr, model, 'exec')
            # Resolve local symbol
            else:
                return str(model.get(eexpr, '???{0}{1}???'.format(etype, eexpr)))
        except:  # Catch All Errors/Exceptions
            log(traceback.format_exc())
            log("Error executing expression {0} in template {1}".format(eexpr, path))
            return 'Error:' + traceback.format_exc()

    return eval_expr


def template_mapper(*base_path, model=None):
    """
    Main Template Engine Mapper (include)
    """

    base_path = base_path[:-1]

    def map_template(*path, **params):
        sub_path = base_path + path
        url, context, abs_path = get_resource_url(*sub_path)
        scope = dict(model or {})
        scope.update({'params': DictObject(params)})
        return process_template(abs_path, scope)

    return map_template


def process_template(path, model):
    """
    Load template from path and evaluate it
    """

    (html, macros) = get_template(path)
    scope = dict(model or {})
    for name, builder in macros.items():
        scope[name] = builder(scope)

    evaluator = template_expression_evaluator(path, scope)
    return TEMPLATE_EXPR_PATTERN.sub(evaluator, html)


def parse_macros(code, path):
    """
    Main Template Engine: Parse macros into callable functions
    """

    macros = {}

    def save_macro(match):
        name = match.group(1)
        code = match.group(2)
        macros[name] = template_macro(name, code, path)
        return ""

    parsed = TEMPLATE_MACRO_PATTERN.sub(save_macro, code)
    return parsed, macros


def parse_blocks(code, path):
    """
    Main Template Engine: Parse python blocks into callable functions
    """
    blocks = {}

    def compile_block(match):
        block = textwrap.dedent(match.group(1))
        name = "block_{0}_{1}".format(random.randint(0, 65000), int(time.time()))
        blocks[name] = template_macro(name, block, path)
        return '${x:' + block + '()}'

    parsed = TEMPLATE_EXEC_PATTERN.sub(compile_block, code)
    return parsed, blocks


def get_template(path):
    """
    Main Template Engine Parser
    """

    with open(path) as f:
        # Read all template code
        code = f.read()
        # Compile all blocks
        code, blocks = parse_blocks(code, path)
        # Parse all macros
        code, macros = parse_macros(code, path)
        # Merge macros ad blocks
        macros.update(blocks)
        return code, macros


def render(*path, model):
    """
    Main Template Engine Renderer
    """

    url, context, abs_path = get_resource_url(*path)
    model['_URL_'] = url
    model['_BASE_'] = context
    model['_FILE_'] = abs_path
    model['include'] = template_mapper(abs_path, model=model)
    model['tr'] = tr
    model['comp'] = components
    model['urlencode'] = quote
    model['sha256'] = sha256
    return process_template(abs_path, model=model), url
