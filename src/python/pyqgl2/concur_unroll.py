# Copyright 2015 by Raytheon BBN Technologies Corp.  All Rights Reserved.

"""
Unroll for loops (and possibly other conditional/iterative statements)
within a "with concur" block.
"""

import ast
import os
import sys

from copy import deepcopy

import pyqgl2.ast_util

from pyqgl2.ast_util import NodeError
from pyqgl2.lang import QGL2

def is_concur(node):
    """
    Return True if the node is a with-concur block,
    otherwise False
    """

    if not node:
        return False

    if not isinstance(node, ast.With):
        return False

    for item in node.items:
        if (isinstance(item.context_expr, ast.Name) and
                (item.context_expr.id == QGL2.QCONCUR)):
            return True

    return False


class ConcurUnroller(ast.NodeTransformer):
    """
    TODO: document the subset of all possible cases that this
    code actually recognizes/handles
    """

    def __init__(self):

        self.bindings_stack = list()
        self.change_cnt = 0

    def visit_With(self, node):

        if not is_concur(node):
            return self.generic_visit(node) # check

        while True:
            old_change_cnt = self.change_cnt

            new_outer_body = list()

            for outer_stmnt in node.body:
                if isinstance(outer_stmnt, ast.For):
                    unrolled = self.for_unroller(outer_stmnt)
                    new_outer_body += unrolled
                else:
                    new_outer_body.append(outer_stmnt)

            node.body = new_outer_body

            # If we made changes in the last iteration,
            # then the resulting code might have more changes
            # we can make.  Keep trying until we manage to
            # iterate without making any changes.
            #
            if self.change_cnt == old_change_cnt:
                break

        return node

    def visit_Name(self, node):
        """
        If the name has a binding in any local scope (which may
        be nested), then substitute that binding
        """

        name_id = node.id

        for ind in range(len(self.bindings_stack) -1, -1, -1):
            if name_id in self.bindings_stack[ind]:
                self.change_cnt += 1
                return self.bindings_stack[ind][name_id]

        return node

    def for_unroller(self, for_node):

        # The iter has to be an ordinary ast.List.  It is not enough
        # for it to be an expression that evaluates to a list or
        # collection--it has to be a real, naked list, so we know
        # exactly how long it is.
        #
        # Right now we need it to consist of literals (possibly grouped
        # in tuples or similar simple structures).  Hopefully we'll relax
        # this to include things like range() expressions where the
        # parameters are known.

        if for_node.orelse:
            print('WARNING: cannot expand for with orelse') # FIXME
            return list([for_node])

        if not isinstance(for_node.iter, ast.List):
            return list([for_node])

        # TODO more checking for consistency/fit

        new_stmnts = list()

        vals = for_node.iter.elts
        for index in range(len(vals)):

            try:
                bindings = self.make_bindings(for_node.target, vals[index])
            except TypeError as exc:
                NodeError.error_msg(vals[index], str(exc))
                return new_stmnts # return partial results; bail out later

            # Things to think about: should all the statements that
            # come from the expansion of one pass through the loop
            # be grouped in some way (such as a 'with seq' block)?
            # Or should they just be dumped onto the end, as we do now?

            self.bindings_stack.append(bindings)

            new_body = deepcopy(for_node.body)

            new_stmnts += self.replace_bindings(bindings, new_body)

            self.bindings_stack.pop()

        return new_stmnts

    def make_bindings(self, targets, values):
        """
        make a dictionary of bindings for the "loop variables"

        If the target is a single name, then just assign the values
        to it as a tuple.  If the target is a tuple, then try to match
        up the values to the names in the tuple.

        There are a lot of things that could go wrong here, but we
        don't detect/handle many of them yet

        There's some deliberate sloppiness permitted: the loop target
        can be a list (which is weird style) and the parameters can
        be a combination of lists and tuples.  As long as the target
        and each element of the values can be indexed, things will
        work out.  We could be stricter, because if these types are
        mixed it's almost certainly an error of some kind.
        """

        bindings = dict()

        if isinstance(targets, ast.Name):
            bindings[targets.id] = values
        elif isinstance(targets, ast.Tuple) or isinstance(targets, ast.List):

            # If the target is a list or tuple, then the values must
            # be as well
            #
            if (not isinstance(values, ast.List) and
                    not isinstance(values, ast.Tuple)):
                NodeError.error_msg(values,
                        'if loop vars are a tuple, params must be list/tuple')
                return bindings

            # The target and the values must be the same length
            #
            if len(targets.elts) != len(values.elts):
                NodeError.error_msg(values,
                        'mismatch between length of loop variables and params')
                return bindings

            for index in range(len(targets.elts)):
                name = targets.elts[index].id
                value = values.elts[index]

                bindings[name] = value
        else:
            NodeError.error_msg(targets,
                    'loop target variable must be a name or tuple')

        return bindings

    def replace_bindings(self, bindings, stmnts):

        new_stmnts = list()

        for stmnt in stmnts:
            new_stmnt = self.visit(stmnt)
            new_stmnts.append(new_stmnt)

        return new_stmnts


class QbitGrouper(ast.NodeTransformer):
    """
    TODO: this is just a prototype and needs some refactoring
    """

    def __init__(self):
        pass

    def visit_With(self, node):

        if not is_concur(node):
            return self.generic_visit(node) # check

        print('WITH %s' % ast.dump(node))

        # Hackish way to create a seq node to use
        seq_item_node = deepcopy(node.items[0])
        seq_item_node.context_expr.id = 'seq'
        seq_node = ast.With(items=list([seq_item_node]), body=list())

        groups = self.group_stmnts(node.body)
        new_body = list()

        for qbits, stmnts in groups:
            new_seq = deepcopy(seq_node)
            new_seq.body = stmnts
            new_body.append(new_seq)

        node.body = new_body

        # print('Final:\n%s' % pyqgl2.ast_util.ast2str(node))

        return node

    @staticmethod
    def find_qbits(stmnt):

        qbits = set()

        for node in ast.walk(stmnt):
            if isinstance(node, ast.Name):

                # This is an ad-hoc way to find QBITS, which
                # requires that the substituter has already run
                #
                # TODO: mark names as qbits (and with channel info)
                # without rewriting the names, or keep the original
                # names after rewriting: keep both the original name
                # intact and the qbit assignment so that both can
                # be observed.  This requires changes in the substituter,
                # as well as here.
                #
                if node.id.startswith('QBIT_'):
                    qbits.add(node.id)

        # print('FOUND QBITS [%s] %s' %
        #         (pyqgl2.ast_util.ast2str(stmnt).strip(), str(qbits)))

        return list(qbits)

    @staticmethod
    def group_stmnts(stmnts, find_qbits_func=None):
        """
        Return a list of statement groups, where each group is a tuple
        (qbit_list, stmnt_list) where qbit_list is a list of all of
        the qbits referenced in the statements in stmnt_list.

        The stmnts list is partitioned such that each qbit is referenced
        by statements in exactly one partition (with a special partition
        for statements that don't reference any qbits).

        TODO: Independence is defined ad-hoc here, and will need
        to be something more sophisticated that understands the
        interdependencies between qbits/channels.

        For example, assuming that "x", "y", and "z" refer to
        qbits on non-conflicting channels, the statements:

                X90(x)
                Y90(y)
                Id(z)
                Y90(x)
                X180(z)

        can be grouped into:

                [ [ X90(x), Y90(x) ], [ Y90(y) ], [ Id(z), X180(z) ] ]

        which would result in a returned value of:

        [ ([x], [X90(x), Y90(x)]), ([y], [Y90(y)]), ([z], [Id(z), X180(z)]) ]

        If there are operations over multiple qbits, then the
        partitioning may fail.
        """

        if find_qbits_func is None:
            find_qbits_func = QbitGrouper.find_qbits

        qbit2list = dict()

        for stmnt in stmnts:
            qbits_referenced = find_qbits_func(stmnt)

            if len(qbits_referenced) == 0:
                # print('unexpected: no qbit referenced')

                # Not sure whether this should be an error;
                # for now we'll add this to a special 'no qbit'
                # bucket.

                if 'no_qbit' not in qbit2list:
                    qbit2list['no_qbit'] = list([stmnt])
                else:
                    qbit2list['no_qbit'].append(stmnt)

            elif len(qbits_referenced) == 1:
                qbit = qbits_referenced[0]
                if qbit not in qbit2list:
                    qbit2list[qbit] = list([stmnt])
                else:
                    qbit2list[qbit].append(stmnt)
            else:
                # There are multiple qbits referenced by the stmnt,
                # then we need to find any other stmnt lists that
                # we've built up for each of the qbits, and combine
                # them into one sequence of statments, and then
                # map each qbit to the resulting sequence.
                #
                # This would be more elegant if we could have a set
                # of lists, but in Python lists aren't hashable,
                # so we need to fake a set implementation with a list.
                #
                stmnt_set = list()
                stmnt_list = list()

                for qbit in qbits_referenced:
                    if qbit in qbit2list:
                        curr_list = qbit2list[qbit]

                        if curr_list not in stmnt_set:
                            stmnt_set.append(curr_list)

                for seq in stmnt_set:
                    stmnt_list += seq

                stmnt_list.append(stmnt)

                for qbit in qbits_referenced:
                    qbit2list[qbit] = stmnt_list

        # neaten up qbit2list to eliminate duplicates;
        # present the result in a more useful manner

        tmp_groups = dict()

        for qbit in qbit2list.keys():
            # this is gross, but we can't use a mutable object as a key
            # in a table, so we use a string representation

            stmnts_str = str(qbit2list[qbit])
            if stmnts_str in tmp_groups:
                (qbits, stmnts) = tmp_groups[stmnts_str]
                qbits.append(qbit)
            else:
                tmp_groups[stmnts_str] = (list([qbit]), qbit2list[qbit])

        groups = [ (sorted(tmp_groups[key][0]), tmp_groups[key][1])
                for key in tmp_groups.keys() ]

        return sorted(groups)

if __name__ == '__main__':

    basic_tests = [
            [ """ Basic test """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        foo(x)
""",
"""
with concur:
    foo(QBIT_1)
    foo(QBIT_2)
    foo(QBIT_3)
"""
            ],

            [ """ Double Nested loops """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        for y in [4, 5, 6]:
            foo(x, y)
""",
"""
with concur:
    foo(QBIT_1, 4)
    foo(QBIT_1, 5)
    foo(QBIT_1, 6)
    foo(QBIT_2, 4)
    foo(QBIT_2, 5)
    foo(QBIT_2, 6)
    foo(QBIT_3, 4)
    foo(QBIT_3, 5)
    foo(QBIT_3, 6)
"""
            ],

            [ """ Triple Nested loops """,
"""
with concur:
    for x in [QBIT_1, QBIT_2]:
        for y in [QBIT_3, QBIT_4]:
            for z in [5, 6]:
                foo(x, y, z)
""",
"""
with concur:
    foo(QBIT_1, QBIT_3, 5)
    foo(QBIT_1, QBIT_3, 6)
    foo(QBIT_1, QBIT_4, 5)
    foo(QBIT_1, QBIT_4, 6)
    foo(QBIT_2, QBIT_3, 5)
    foo(QBIT_2, QBIT_3, 6)
    foo(QBIT_2, QBIT_4, 5)
    foo(QBIT_2, QBIT_4, 6)
"""
            ],
            [ """ Basic compound test """,
"""
with concur:
    for x in [QBIT_1, QBIT_2, QBIT_3]:
        foo(x)
        bar(x)
""",
"""
with concur:
    foo(QBIT_1)
    bar(QBIT_1)
    foo(QBIT_2)
    bar(QBIT_2)
    foo(QBIT_3)
    bar(QBIT_3)
"""
            ],
            [ """ Nested compound test """,
"""
with concur:
    for x in [1, 2]:
        for y in [3, 4]:
            foo(x)
            bar(y)
""",
"""
with concur:
    foo(1)
    bar(3)
    foo(1)
    bar(4)
    foo(2)
    bar(3)
    foo(2)
    bar(4)
"""
            ],
            [ """ Simple tuple test """,
"""
with concur:
    for x, y in [(1, 2), (3, 4)]:
        foo(x, y)
""",
"""
with concur:
    foo(1, 2)
    foo(3, 4)
"""
            ],
            [ """ Simple tuple test 2 """,
"""
with concur:
    for x, y in [(QBIT_1, QBIT_2), (QBIT_3, QBIT_4)]:
        foo(x)
        foo(y)
""",
"""
with concur:
    foo(QBIT_1)
    foo(QBIT_2)
    foo(QBIT_3)
    foo(QBIT_4)
"""
            ],
            [ """ Compound test 2 """,
"""
with concur:
    for x in [QBIT_1, QBIT_2]:
        for y in [3, 4]:
            foo(x, y)

            for z in [5, 6]:
                bar(x, y, z)
""",
"""
with concur:
    foo(QBIT_1, 3)
    bar(QBIT_1, 3, 5)
    bar(QBIT_1, 3, 6)
    foo(QBIT_1, 4)
    bar(QBIT_1, 4, 5)
    bar(QBIT_1, 4, 6)
    foo(QBIT_2, 3)
    bar(QBIT_2, 3, 5)
    bar(QBIT_2, 3, 6)
    foo(QBIT_2, 4)
    bar(QBIT_2, 4, 5)
    bar(QBIT_2, 4, 6)
"""
            ],

            [ """ expression test """,
"""
with concur:
    for x in [1, 2]:
        for y in [3, 4]:
            foo(x + y)
""",
# extra level of parens needed for the pretty-printer
"""
with concur:
    foo((1 + 3))
    foo((1 + 4))
    foo((2 + 3))
    foo((2 + 4))
"""
            ],

        ]


    def test_case(description, in_txt, out_txt):
        ptree = ast.parse(in_txt, mode='exec')
        unroller = ConcurUnroller()
        new_ptree = unroller.visit(ptree)
        new_txt = pyqgl2.ast_util.ast2str(new_ptree)

        body = new_ptree.body[0].body
        # print('body %s' % ast.dump(body))

        grouper = QbitGrouper()
        redo = grouper.visit(new_ptree)

        partitions = grouper.group_stmnts(body)
        print('partitions: %s' % str(partitions))
        # for pid in partitions:
        #     print('[%s]\n%s' %
        #             (pid, pyqgl2.ast_util.ast2str(partitions[pid]).strip()))


        if out_txt.strip() != new_txt.strip():
            print('FAILURE: %s\n:[%s]\n----\n[%s]' %
                    (description, out_txt, new_txt))
            return False
        else:
            print('SUCCESS: %s' % description)
            return True

    def preprocess(fname):
        text = open(fname, 'r').read()
        ptree = ast.parse(text, mode='exec')

        print('INITIAL PTREE:\n%s' % pyqgl2.ast_util.ast2str(ptree))

        unroller = ConcurUnroller()
        new_ptree = unroller.visit(ptree)

        print('NEW PTREE:\n%s' % pyqgl2.ast_util.ast2str(new_ptree))

        # Now do the transformation

    def test_grouping1():

        def simple_find_qbits(stmnt):
            """
            debugging impl of find_qbits, for simple quasi-statements.

            Assumes that the stmnt is a tuple consisting of a list
            (of qbit numbers) and a string (the description of the statement)
            So finding the qbits is done by returning the first element
            of the tuple.

            See simple_stmnt_list below for an example.
            """

            return stmnt[0]

        simple_stmnt_list = [
                ( [1], 'one-1' ),
                ( [1], 'one-2' ),
                ( [2], 'two-1' ),
                ( [1], 'one-3' ),
                ( [2], 'two-2' ),
                ( [3], 'three-1' ),
                ( [4], 'four-1' ),
                ( [3, 4], 'threefour-1' )
                ]

        res = QbitGrouper.group_stmnts(simple_stmnt_list,
                find_qbits_func=simple_find_qbits)

        for stmnt_list in res:
            print('STMNT_LIST %s' % str(stmnt_list))

    def main():

        test_grouping1()

        for (description, in_txt, out_txt) in basic_tests:
            test_case(description, in_txt, out_txt)

        if len(sys.argv) > 1:
            for fname in sys.argv[1:]:
                preprocess(fname)

    main()
