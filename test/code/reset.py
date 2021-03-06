from qgl2.qgl2 import qgl2decl, qgl2main
from qgl2.qgl2 import classical, pulse, qreg, QRegister
from qgl2.qgl1 import Id, X90, Y90, X, Y, Z, MEAS

@qgl2decl
def reset1():
    q = QRegister('q1')
    m = MEAS(q)
    if m:
        X(q)
    else:
        Id(q)
    X90(q)

@qgl2decl
def reset2():
    q = QRegister('q1')
    m = MEAS(q)
    if not m:
        X(q)
    else:
        Id(q)
    X90(q)

@qgl2decl
def reset3():
    q = QRegister('q1')
    m = MEAS(q)
    if m == 2:
        X(q)
    else:
        Id(q)
    X90(q)

@qgl2decl
def reset4():
    q = QRegister('q1')
    m = MEAS(q)
    if m > 1:
        X(q)
    else:
        Id(q)
    X90(q)

@qgl2decl
def reset5():
    q = QRegister('q1')
    m = MEAS(q)
    # TODO inject an Id into the else clause
    if m == 1:
        X(q)
    X90(q)

@qgl2decl
def runtime1():
    q = QRegister('q1')
    m1 = MEAS(q)
    m2 = MEAS(q)
    r = my_operator(m1, m2)
    if r == 1:
        X(q)
    else:
        Z(q)
