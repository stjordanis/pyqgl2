#!/usr/bin/env python3
#
# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import os
import sys

from copy import deepcopy

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
from pyqgl2.check_qbit import CheckType
from pyqgl2.check_waveforms import CheckWaveforms
from pyqgl2.importer import Importer
from pyqgl2.lang import QGL2

class SubstituteChannel(NodeTransformerWithFname):

    def __init__(self, fname, qbit_bindings, func_defs):
        super(SubstituteChannel, self).__init__(fname)

        self.qbit_map = {name:chan_no for (name, chan_no) in qbit_bindings}
        self.func_defs = func_defs

    def visit_Name(self, node):
        print('VISITING NAME %s' % ast.dump(node))

        if node.id in self.qbit_map:
            node.id = self.qbit_map[node.id]

        return node

    def visit_FunctionDef(self, node):
        """
        This is a shortcut to leap to working on the
        statements of the function instead of doing
        substitution on the parameters and annotations
        of the function

        TODO:
        Eventually we'll have to deal with everything,
        not just the body, and this will have to be
        undone.
        """

        node.body = [self.visit(stmnt) for stmnt in node.body]
        return node

    def visit_Call(self, node):
        # Now we have to map our parameters to this call

        # Find the definition for the function
        #
        # TODO: we're only looking in the current file,
        # not using modules

        fname = node.func.id
        aparams = [arg.id if isinstance(arg, ast.Name) else None
                for arg in node.args]
        print('PARAMS %s actual params %s' % (fname, str(aparams)))

        if fname in self.func_defs:
            (fparams, func_ast) = self.func_defs[fname]
            print('FOUND %s formal params %s' % (fname, str(fparams)))
        else:
            self.error_msg('no definition found for %s' % fname)
            return node

        # map our local bindings to the formal parameters of
        # this function, to create a signature

        # It would be nice if we could do something with kwargs,
        # but we're not even making an attempt right now
        #
        qbit_defs = list()
        if len(fparams) != len(aparams):
            self.error_msg('formal and actual param lists differ in length')
            return node

        print('MY CONTEXT %s' % str(self.qbit_map))

        for ind in range(len(fparams)):
            fparam = fparams[ind]
            aparam = aparams[ind]

            (fparam_name, fparam_type) = fparam.split(':')
            print('fparam %s needs %s' % (fparam_name, fparam_type))

            if (fparam_type == 'qbit') and (aparam not in self.qbit_map):
                self.error_msg(node,
                        'assigned non-qbit to qbit param %s' % fparam_name)
                return node
            elif (fparam_type != 'qbit') and (aparam in self.qbit_map):
                self.error_msg(node,
                        'assigned qbit to non-qbit param %s' % fparam_name)
                return node

            if aparam in self.qbit_map:
                qbit_defs.append((fparam_name, self.qbit_map[aparam]))

        print('MAPPING FOR QBITS %s' % str(qbit_defs))

        # see whether we already have a function that matches
        # the signature.  If not, create one and add it to the
        # symbol table
        #
        # replace this call with a call to the new function
        #
        # return the resulting node
        #
        return node

def specialize(func_node, qbit_defs, func_defs):
    """
    qbit_defs is a list of (fp_name, qref) mappings
    (where fp_name is the name of the formal parameter
    and qref is a reference to a physical qbit)

    func_node is presumed to be a function definition

    returns a new node that contains a function definition
    for a "specialized" version of the function that
    works with that qbit definition.
    """

    print('INITIAL AST %s' % ast.dump(func_node))

    # needs more mangling?
    refs = '_'.join([str(phys_chan) for (fp_name, phys_chan) in qbit_defs])
    mangled_name = func_node.name + '___' + refs

    print('MANGLED NAME %s' % mangled_name)

    # new_func = ast.If(name=mangled_name, 

    sub_chan = SubstituteChannel(func_node.qgl_fname, qbit_defs, func_defs)
    new_func = sub_chan.visit(func_node)
    print('SPECIALIZED %s' % ast.dump(new_func))

    return None

def preprocess(fname, main_name=None):

    importer = Importer(fname)
    ptree = importer.path2ast[importer.base_fname]

    type_check = CheckType(importer.base_fname)
    nptree = type_check.visit(ptree)

    # Find the main function
    qglmain = None
    if main_name:
        if main_name in type_check.func_defs:
            (decls, qglmain) = type_check.func_defs[main_name]
            print('using requested main function [%s]' % main_name)
        else:
            print('requested main function [%s] not found' % main_name)
    else:
        if type_check.qglmain:
            main_name = type_check.qglmain.name
            print('using declared main function [%s]' % main_name)
            (decls, qglmain) = type_check.func_defs[main_name]
        else:
            print('no function declared to be main')

    if not qglmain:
        sys.exit(1)

    specialize(qglmain, [('a', 1), ('b', 20)], type_check.func_defs)

    for func_def in sorted(type_check.func_defs.keys()):
        types, node = type_check.func_defs[func_def]
        call_list = node.qgl_call_list

    if type_check.max_err_level >= NodeError.NODE_ERROR_ERROR:
        print('bailing out 1')
        sys.exit(1)

    sym_check = CheckSymtab(fname, type_check.func_defs)
    nptree2 = sym_check.visit(nptree)

    if sym_check.max_err_level >= NodeError.NODE_ERROR_ERROR:
        print('bailing out 2')
        sys.exit(1)

    wav_check = CheckWaveforms(fname, type_check.func_defs)
    nptree3 = sym_check.visit(nptree2)

    if wav_check.max_err_level >= NodeError.NODE_ERROR_ERROR:
        print('bailing out 3')
        sys.exit(1)

if __name__ == '__main__':
    preprocess(sys.argv[1])