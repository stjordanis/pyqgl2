#!/usr/bin/env python3

# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast

from copy import deepcopy

# For testing only
if __name__ == '__main__':
    import os
    import sys

    # Find the directory that this executable lives in;
    # munge the path to look within the parent module
    #
    DIRNAME = os.path.normpath(
            os.path.abspath(os.path.dirname(sys.argv[0]) or '.'))
    sys.path.append(os.path.normpath(os.path.join(DIRNAME, '..')))

from pyqgl2.ast_util import NodeError
from pyqgl2.ast_util import NodeTransformerWithFname
from pyqgl2.ast_util import NodeVisitorWithFname
from pyqgl2.check_symtab import CheckSymtab

class FuncParam(object):

    def __init__(self, name):
        self.name = name
        self.value = None

class QuantumFuncParam(FuncParam):
    pass

class ClassicalFuncParam(FuncParam):
    pass

class CheckType(NodeTransformerWithFname):

    def __init__(self, fname):
        super(CheckType, self).__init__(fname)

        # for each qbit, track where it is created
        #
        # the key is the qbit number, and the val is the name
        # and where it's created
        #
        self.qbit_origins = dict()

        # a list of scope tuples: (name, qbit?, context)
        #
        # We begin with the global scope, initially empty
        #
        self.scope = list(list())

        self.func_defs = dict()

        self.func_level = 0

        self.waveforms = dict()

        # Reference to the main function, if any
        #
        self.qglmain = None

        self.qgl_call_stack = list()

    def _push_scope(self, qbit_scope):
        self.scope.append(qbit_scope)

    def _pop_scope(self):
        self.scope = self.scope[:-1]

    def _qbit_scope(self):
        return self.scope[-1]

    def _extend_scope(self, name):
        self.scope[-1].append(name)

    def _qbit_decl(self, node):

        q_args = list()
        q_return = None

        if type(node) != ast.FunctionDef:
            return None

        if node.returns:
            ret = node.returns

            # It would be nice to be able to return a qbit
            # tuple, maybe.
            #
            if ((type(ret) == ast.Name) and (ret.id == 'qbit')):
                q_return = 'qbit'
            else:
                self.warning_msg(node,
                        'unexpected annotation [%s]' % ast.dump(ret))

        if node.args.args:
            for arg in node.args.args:
                print('>> %s' % ast.dump(arg))

                name = arg.arg
                annotation = arg.annotation
                if not annotation:
                    q_args.append('%s:classical' % name)
                    continue

                if type(annotation) == ast.Name:
                    if annotation.id == 'qbit':
                        q_args.append('%s:qbit' % name)
                    else:
                        self.warning_msg(node, 'unexpected annotation [%s]' %
                                annotation.id)
                else:
                    self.warning_msg(node, 'unexpected annotation [%s]' %
                            ast.dump(annotation))

        node.q_args = q_args
        node.q_return = q_return

        return q_args

    def gen_waveform(self, name, args, kwargs):
        arg_text = ', '.join([ast.dump(arg) for arg in args])
        kwarg_text = ', '.join(sorted([ast.dump(arg) for arg in kwargs]))

        errs = 0
        for arg_index in range(1, len(args)):
            if type(args[arg_index]) != ast.Num:
                self.error_msg(arg, 'arg %d must be a number' % arg_index)
                errs += 1

        if errs:
            return

        signature = '%s-%s' % (name, arg_text)
        if kwarg_text:
            signature += '-%s' % kwarg_text

        # print 'WAVEFORM %s %s %s' % (name, arg_text, kwarg_text)
        # print signature

        if signature in self.waveforms:
            print('NOTE: already generated waveform %s' % signature)
        else:
            print('generating waveform %s' % signature)
            self.waveforms[signature] = 1 # BOGUS

    def assign_simple(self, node):

        target = node.targets[0]
        value = node.value

        if type(target) != ast.Name:
            return node

        if target.id in self._qbit_scope():
            msg = 'reassignment of qbit \'%s\' forbidden' % target.id
            self.error_msg(node,
                    ('reassignment of qbit \'%s\' forbidden' % target.id))

        if (type(value) == ast.Call) and (value.func.id == 'Qbit'):
            self._extend_scope(target.id)
        elif (type(value) == ast.Name) and value.id in self._qbit_scope():
            self.warning_msg(node, 'alias of qbit \'%s\' as \'%s\'' %
                    (value.id, target.id))
            self._extend_scope(target.id)
        else:
            return node

        print('qbit scope %s' % str(self._qbit_scope()))

        return node

    def visit_Assign(self, node):

        # We only do singleton assignments, not tuples,
        # and not expressions

        if type(node.targets[0]) == ast.Name:
            self.assign_simple(node)

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):

        # print('>>> %s' % ast.dump(node))

        # Initialize the called functions list for this
        # definition, and then push this context onto
        # the call stack.  The call stack is a stack of
        # call lists, with the top of the stack being
        # the current function at the top and bottom
        # of each function definition.
        #
        # We do this for all functions, not just QGL functions,
        # because we might want to be able to analyze non-QGL
        # functions
        #
        self.qgl_call_stack.append(list())

        qglmain = False
        qglfunc = False
        other_decorator = False

        if node.decorator_list:
            for dec in node.decorator_list:

                # qglmain implies qglfunc, but it's permitted to
                # have both
                #
                if (type(dec) == ast.Name) and (dec.id == 'qglmain'):
                    qglmain = True
                    qglfunc = True
                elif (type(dec) == ast.Name) and (dec.id == 'qglfunc'):
                    qglfunc = True
                else:
                    other_decorator = True

            if qglfunc and other_decorator:
                self.error_msg(node, 'unrecognized decorator with qglfunc')

        if qglmain:
            print('qblmain detected')
            if self.qglmain:
                omain = self.qglmain
                self.error_msg(node, 'more than one qglmain function')
                self.error_msg(node,
                        'previous qglmain %s:%d:%d' %
                        (omain.fname, omain.lineno, omain.col_offset))
                self._pop_scope()
                self.qgl_call_stack.pop()
                return node
            else:
                node.fname = self.fname
                self.qglmain = node

        if self.func_level > 0:
            self.error_msg(node, 'qgldef functions cannot be nested')

        # So far so good: now actually begin to process this node

        decls = self._qbit_decl(node)
        if decls is not None:
            # diagnostic only
            self.diag_msg(
                    node, '%s declares qbits %s' % (node.name, str(decls)))
            self._push_scope(decls)
        else:
            self._push_scope(list())

        self.func_level += 1
        self.generic_visit(node)
        self.func_level -= 1

        # make a copy of this node and its qbit scope

        node.qgl_call_list = self.qgl_call_stack.pop()

        self.func_defs[node.name] = (self._qbit_scope(), deepcopy(node))

        self._pop_scope()

        self.diag_msg(node,
                'call stack %s: %s' %
                (node.name, str(', '.join([call.func.id
                    for call in node.qgl_call_list]))))
        return node

    def visit_Call(self, node):

        # We can only check functions referenced by name, not arbitrary
        # expressions that return a function
        #
        if type(node.func) != ast.Name:
            self.error_msg(node, 'function not referenced by name')
            return node

        node.qgl_scope = self._qbit_scope()[:]

        self.qgl_call_stack[-1].append(node)

        return node

class CompileQGLFunctions(ast.NodeTransformer):

    LEVEL = 0

    def __init__(self, *args, **kwargs):
        super(CompileQGLFunctions, self).__init__(*args, **kwargs)

        self.concur_finder = FindConcurBlocks()

    def visit_FunctionDef(self, node):
        qglmain = False
        qglfunc = False
        other_decorator = False

        print('>>> %s' % ast.dump(node))

        if node.decorator_list:
            print('HAS DECO')
            for dec in node.decorator_list:
                print('HAS DECO %s' % str(dec))

                # qglmain implies qglfunc, but it's permitted to
                # have both
                #
                if (type(dec) == ast.Name) and (dec.id == 'qglmain'):
                    qglmain = True
                    qglfunc = True
                elif (type(dec) == ast.Name) and (dec.id == 'qglfunc'):
                    qglfunc = True
                else:
                    other_decorator = True

            if qglfunc and other_decorator:
                self.error_msg(node, 'unrecognized decorator with qglfunc')

        if not qglfunc:
            return node

        if qglmain:
            print('qblmain detected')
            if self.qglmain:
                omain = self.qglmain
                self.error_msg(node, 'more than one qglmain function')
                self.error_msg(node,
                        'previous qglmain %s:%d:%d' %
                        (omain.fname, omain.lineno, omain.col_offset))
                return node
            else:
                node.fname = self.fname
                self.qglmain = node

        if self.LEVEL > 0:
            self.error_msg(node, 'QGL mode functions cannot be nested')

        self.LEVEL += 1
        # check for nested qglfunc functions
        self.generic_visit(node)
        self.LEVEL -= 1

        # First, find and check all the concur blocks

        body = node.body
        for ind in range(len(body)):
            stmnt = body[ind]
            body[ind] = self.concur_finder.visit(stmnt)

class FindWaveforms(ast.NodeTransformer):

    def __init__(self, *args, **kwargs):
        super(FindWaveforms, self).__init__(*args, **kwargs)

        self.seq = list()

    def visit_Call(self, node):

        # This is just a sketch

        if node.func.id == 'MEAS':
            self.seq.append('MEAS ' + ast.dump(node))
        elif node.func.id == 'X90':
            self.seq.append('X90 ' + ast.dump(node))
        elif node.func.id == 'Y90':
            self.seq.append('Y90 ' + ast.dump(node))

        return node


class FindConcurBlocks(ast.NodeTransformer):

    LEVEL = 0

    def __init__(self, *args, **kwargs):
        super(FindConcurBlocks, self).__init__(*args, **kwargs)

        self.concur_stmnts = set()
        self.qbit_sets = dict()

    def visit_With(self, node):
        if ((type(node.context_expr) != ast.Name) or
                (node.context_expr.id != 'concur')):
            return node

        if self.LEVEL > 0:
            self.error_msg(node, 'nested concur blocks are not supported')

        self.LEVEL += 1

        body = node.body
        for ind in range(len(body)):
            stmnt = body[ind]
            find_ref = FindQbitReferences()
            find_ref.generic_visit(stmnt)
            self.qbit_sets[ind] = find_ref.qbit_refs

            self.visit(stmnt)

        self.LEVEL -= 1

        # check_conflicts will halt the program if it detects an error
        #
        qbits_referenced = self.check_conflicts(node.lineno)
        print('qbits in concur block (line: %d): %s' % (
                node.lineno, str(qbits_referenced)))

        for ind in range(len(body)):
            stmnt = body[ind]
            find_waveforms = FindWaveforms()
            find_waveforms.generic_visit(stmnt)

            for waveform in find_waveforms.seq:
                print('concur %d: WAVEFORM: %s' % (stmnt.lineno, waveform))

    def check_conflicts(self, lineno):

        all_seen = set()

        for refs in self.qbit_sets.values():
            if not refs.isdisjoint(all_seen):
                conflict = refs.intersection(all_seen)
                self.error_msg(node,
                        '%s appear in multiple concurrent statements' %
                        str(', '.join(list(conflict))))

            all_seen.update(refs)

        return all_seen

class FindQbitReferences(ast.NodeTransformer):
    """
    Find all the references to qbits in a node

    Assumes that all qbits are referenced by variables with
    names that start with 'qbit', rather than arbitrary expressions

    For example, if you do something like

        arr[ind] = qbit1
        foo = arr[ind]

    Then "qbit1" will be detected as a reference to a qbit,
    but "arr[ind]" or "foo" will not, even though all three
    expressions evaluate to a reference to the same qbit.
    """

    def __init__(self, *args, **kwargs):
        super(FindQbitReferences, self).__init__(*args, **kwargs)

        self.qbit_refs = set()

    def visit_Name(self, node):
        if node.id.startswith('qbit'):
            self.qbit_refs.add(node.id)

        return node

if __name__ == '__main__':
    import sys

    def preprocess(fname):

        text = open(fname, 'r').read()

        ptree = ast.parse(text, mode='exec')
        print(ast.dump(ptree))

        type_check = CheckType(fname)

        nptree = type_check.visit(ptree)

        for func_def in sorted(type_check.func_defs.keys()):
            types, node = type_check.func_defs[func_def]
            call_list = node.qgl_call_list

            print('%s -> %s' %
                    (node.name, ', '.join(node.func.id for node in call_list)))

        if type_check.max_err_level >= NodeError.NODE_ERROR_ERROR:
            print('bailing out')
            sys.exit(1)

        sym_check = CheckSymtab(fname, type_check.func_defs)
        nptree2 = sym_check.visit(nptree)

    preprocess(sys.argv[1])
