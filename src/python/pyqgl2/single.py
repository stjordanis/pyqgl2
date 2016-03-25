# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import ast
import os
import sys

from copy import deepcopy

from pyqgl2.ast_util import ast2str, NodeError
from pyqgl2.concur_unroll import is_concur, is_seq, find_all_channels
from pyqgl2.importer import collapse_name
from pyqgl2.lang import QGL2

class SingleSequence(object):
    """
    Create a sequence list for a single QBIT

    Note: this assumes that the AST is for one function
    definition that has already been inlined, successfully
    flattened, grouped, and sequenced already.
    """

    def __init__(self):

        self.qbits = set()
        self.qbit_creates = list()
        self.sequence = list()

    def is_qbit_create(self, node):
        """
        If the node does not represent a qbit creation and assignment,
        return False.  Otherwise, return a triple (sym_name, use_name,
        node) where sym_name is the symbolic name, use_name is the
        name used by the preprocessor to substitute for this qbit
        reference, and node is the node parameter (i.e. the root
        of the ast for the assignment.

        There are several sloppy assumptions here.
        """

        if not isinstance(node, ast.Assign):
            return False

        # Only handles simple assignments; not tuples
        # TODO: handle tuples
        if len(node.targets) != 1:
            return False

        if not isinstance(node.value, ast.Call):
            return False

        if not isinstance(node.value.func, ast.Name):
            return False

        # This is the old name, and needs to be updated
        # TODO: update to new name/signature
        if node.value.func.id != 'Qbit':
            return False

        print('FS %s' % ast.dump(node))

        # HACK FIXME: assumes old-style Qbit allocation
        sym_name = node.targets[0].id
        use_name = 'QBIT_%d' % node.value.args[0].n
        return (sym_name, use_name, node)

    def find_sequence(self, node):

        if not isinstance(node, ast.FunctionDef):
            NodeError.fatal_msg(node, 'not a function definition')
            return False

        self.qbits = find_all_channels(node)
        print('FS %s' % str(type(self.qbits)))

        if len(self.qbits) == 0:
            NodeError.error_msg(node, 'no channels found')
            return False
        elif len(self.qbits) > 1:
            NodeError.error_msg(node, 'more than one channel found')
            return False

        for stmnt in node.body:
            assignment = self.is_qbit_create(stmnt)
            if assignment:
                self.qbit_creates.append(assignment)
                continue
            elif is_concur(stmnt):
                if is_seq(stmnt.body[0]):
                    self.sequence += stmnt.body[0].body
                else:
                    NodeError.diag_msg(stmnt.body[0], 'expected seq?')
            else:
                NodeError.diag_msg(stmnt, 'orphan statement')

        return True

    def emit_function(self, func_name='doit'):
        """
        Create a function that, when run, creates the context
        in which the sequence is evaluated, and evaluate it.

        func_name is the name for the function, if provided.
        I'm not certain that the name has any significance
        or whether this function will be, for all practical
        purposes, a lambda.
        """

        # assumes a standard 4-space indent; if the surrounding
        # context uses some other indentation scheme, the interpreter
        # may gripe, and pep8 certainly will
        #
        indent = '    '

        # allow QBIT parameters to be overridden
        #
        preamble = 'def %s(**kwargs)\n' % func_name

        for (sym_name, _use_name, node) in self.qbit_creates:
            preamble += indent + 'if \'' + sym_name + '\' in kwargs:\n'
            preamble += (2 * indent) + sym_name
            preamble += ' = kwargs[\'%s\']\n' % sym_name
            preamble += indent + 'else:\n'
            preamble += (2 * indent) + ast2str(node).strip() + '\n'

        for (sym_name, use_name, _node) in self.qbit_creates:
            preamble += indent + '%s = %s\n' % (use_name, sym_name)

        print('FS PRE\n%s' % preamble)


        sequence = [ast2str(item).strip() for item in self.sequence]

        # TODO there must be a more elegant way to indent this properly
        seq_str = indent + 'seq = [\n' + 2 * indent
        seq_str += (',\n' + 2 * indent).join(sequence)
        seq_str += '\n' + indent + ']\n'

        print('SEQ:\n<<%s>>' % seq_str)

        postamble = indent + 'return seq\n'

        res =  preamble + seq_str + postamble
        print('---\n%s---' % res)

