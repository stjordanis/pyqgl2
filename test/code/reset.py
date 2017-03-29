from qgl2.qgl2 import concur, qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qbit, qbit_list
from qgl2.qgl1 import QubitFactory, Id, X90, Y90, X, Y, MEAS

# FIXME these are inserted by the flattener, the user shouldn't have to
# import them manually
from qgl2.qgl1 import LoadCmp, CmpEq, CmpNeq, CmpGt, CmpLt, Goto, BlockLabel

@qgl2decl
def reset1():
    q = QubitFactory('q1')
    m = MEAS(q)
    if m:
        X(q)
    else:
        Id(q)
    X90(q)

@qgl2decl
def reset2():
    q = QubitFactory('q1')
    m = MEAS(q)
    if not m:
        X(q)
    else:
        Id(q)
    X90(q)

@qgl2decl
def reset3():
    q = QubitFactory('q1')
    m = MEAS(q)
    if m == 2:
        X(q)
    else:
        Id(q)
    X90(q)

@qgl2decl
def reset4():
    q = QubitFactory('q1')
    m = MEAS(q)
    if m > 1:
        X(q)
    else:
        Id(q)
    X90(q)

@qgl2decl
def reset5():
    q = QubitFactory('q1')
    m = MEAS(q)
    # TODO inject an Id into the else clause
    if m == 1:
        X(q)
    X90(q)
