'''
Copyright 2017 Raytheon BBN Technologies

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import ast
from pyqgl2.lang import QGL2
from pyqgl2.debugmsg import DebugMsg
from pyqgl2.ast_util import NodeError, ast2str

class QRegister(object):
    """
    Registers of Qubits.

    Use QRegister.factory() to create instances from AST nodes.
    """

    # mapping from index to reference
    KNOWN_QUBITS = dict()
    NUM_REGISTERS = 0

    def __init__(self, *args):
        '''
        Valid constructor calls:
            QRegister(N) where N is an integer
          Or mix and match or use lists or tuples of:
            QRegister("q2", "q5", ...) where the strings are the names of Qubits
            QRegister(qr1, qr2, qr3, ...) where each object is a QRegister
            QRegister(q1, q2, ...) where each object is a QGL Qubit
        NOTE: Qubit names must currently be of the form "q<int>"
        '''

        self.qubits = []
        if len(args) == 0:
            raise NameError("Must provide at least one argument to QRegister()")
        elif len(args) == 1 and isinstance(args[0], int):
            # width declaration
            N = args[0]
            # find the N lowest qubit indices we haven't used yet
            ct = 1
            while len(self.qubits) < N:
                if ct not in QRegister.KNOWN_QUBITS:
                    self.qubits.append(ct)
                ct += 1
        else:
            for x in args:
                self.addArg(x, args)

        # add qubits to KNOWN_QUBITS
        for q in self.qubits:
            QRegister.KNOWN_QUBITS[q] = None

        QRegister.NUM_REGISTERS += 1
        self.reg_name = 'QREG_' + str(QRegister.NUM_REGISTERS)

    def addArg(self, x, args):
        """Parse one argument to the QRegister constructor. A recursive function."""
        # Careful; avoid global import of QGL1 stuff from QGL2
        from QGL.Channels import Qubit
        if hasattr(x, "__iter__") and not isinstance(x, str) and not isinstance(x, QRegister):
            for xx in x:
                self.addArg(xx, args)
        elif isinstance(x, QRegister):
            # duplicates the QRegister; allows failsafe creating QRegister whatever the arg
            for q in x.qubits:
                if q not in self.qubits:
                    self.qubits.append(q)
                else:
                    # Duplicate - skip
                    # FIXME: Print warning?
                    pass
        elif isinstance(x, str):
            # assume names are of the form "qN"
            # TODO throw an error if the provided string doesn't have that form
            try:
                idx = int(x[1:])
            except ValueError as ve:
                raise ValueError(f"QRegister names must be of the form q<int>: '{x}' (from args {args})")
            if idx not in self.qubits:
                self.qubits.append(idx)
            else:
                # duplicate - skip
                pass
        elif isinstance(x, Qubit):
            # assume names are of the form "qN"
            # TODO throw an error if the provided string doesn't have that form
            try:
                idx = int(x.label[1:])
            except ValueError as ve:
                raise ValueError(f"QRegister names must be of the form q<int>: '{x}' (from args {args})")
            if idx not in self.qubits:
                self.qubits.append(idx)
            else:
                # duplicate - skip
                # FIXME: Print warning?
                pass
        elif isinstance(x, QReference):
            self.addArg(x.ref.qubits[x.idx], args)
        elif isinstance(x, int):
            if x not in self.qubits:
                self.qubits.append(x)
            else:
                # duplicate - skip
                pass
        else:
            raise NameError(f"Invalid QRegister constructor 'QRegister({args})'; arg {x} unknown.")

    def __repr__(self):
        return str(self)

    def __str__(self):
        args = ", ".join("'q{}'".format(q) for q in self.qubits)
        return "QRegister({})".format(args)

    def __eq__(self, other):
        return self.qubits == other.qubits

    def __hash__(self):
        return hash(tuple(self.qubits))

    def use_name(self, idx=None):
        if idx is not None:
            return 'QBIT_' + str(self.qubits[idx])
        else:
            return self.reg_name

    def __len__(self):
        return len(self.qubits)

    def __getitem__(self, n):
        return QReference(self, n)

    def __add__(self, other):
        return QRegister(self, other)

    def __iter__(self):
        for n in range(len(self.qubits)):
            yield self[n]

    @staticmethod
    def factory(node, local_vars):
        '''
        Evaluates a ast.Call node of a QRegister and returns its value.

        local_vars is a dictionary of symbol -> value bindings
        '''
        if not is_qbit_create(node):
            NodeError.error_msg(node,
                "Attempted to create a QRegister from an invalid AST node [%s]." % ast2str(node))

        # convert args into values
        arg_values = []
        for arg in node.value.args:
            if isinstance(arg, ast.Num):
                arg_values.append(arg.n)
            elif isinstance(arg, ast.Str):
                arg_values.append(arg.s)
            elif isinstance(arg, ast.Name) and arg.id in local_vars:
                arg_values.append(local_vars[arg.id])
            elif is_qbit_subscript(arg, local_vars):
                # evaluate the subscript to extract the referenced qubits
                parent_qreg = local_vars[arg.value.id]
                try:
                    arg_val = eval(ast2str(arg), None, local_vars)
                except:
                    NodeError.error_msg(node,
                        "Unhandled qreg subscript [%s]" % ast2str(arg))
                sub_qubits = parent_qreg.qubits[arg_val.idx]
                if hasattr(sub_qubits, '__iter__'):
                    arg_values.extend("q" + str(n) for n in sub_qubits)
                else:
                    arg_values.append("q" + str(sub_qubits))
            else:
                NodeError.error_msg(node,
                    "Unhandled argument to QRegister [%s]" % ast2str(arg))

        return QRegister(*arg_values)

    @classmethod
    def reset(cls):
        cls.KNOWN_QUBITS.clear()
        cls.NUM_REGISTERS = 0

class QReference(object):
    '''
    A subscripted QRegister
    '''
    def __init__(self, ref, idx):
        if not isinstance(ref, QRegister):
            raise NameError("ref is not a QRegister %s" % str(ref))
        self.ref = ref
        self.idx = idx

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "QReference({0}, {1})".format(self.ref, self.idx)

    def __eq__(self, other):
        return (self.ref == other.ref) and (self.idx == other.idx)

    def __len__(self):
        x = self.ref.qubits[self.idx]
        if isinstance(x, int):
            return 1
        else:
            return len(x)

    def __hash__(self):
        return hash(self.ref) + hash(self.idx)

    def use_name(self):
        return self.ref.use_name()

def is_qbit_create(node):
    """
    Returns True if node represents a qbit creation and assignment.

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

    if node.value.func.id != QGL2.QBIT_ALLOC:
        return False

    return True

def is_qbit_subscript(node, local_vars):
    """
    Returns True if a node represents a QRegister subscript
    """
    if not isinstance(node, ast.Subscript):
        return False

    if not node.value.id in local_vars:
        return False

    if not isinstance(local_vars[node.value.id], QRegister):
        return False

    return True
