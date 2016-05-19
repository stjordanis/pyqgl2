
from qgl2.qgl2 import concur, qbit, qgl2decl
from qgl2.qgl2 import sequence, pulse, qgl2main, classical

from qgl2.qgl1 import QubitFactory, X90, Y90, X, MEAS, Utheta, Xtheta
from qgl2.qgl1 import Call, BlockLabel, Goto, LoadRepeat, Repeat, Return
from qgl2.qgl1 import CmpEq

from qgl2.util import init

@qgl2decl
def func_a(q: qbit, a: classical, b: classical):
    func_b(q, a + b, a - b)

@qgl2decl
def func_b(q: qbit, amp: classical, phase: classical):
    Xtheta(q, xx=amp, yy=phase)

@qgl2main
def main():

    x = QubitFactory('1')

    for i, j in [(1, 2), (3, 4)]:
        for k in range(j):
            if MEAS(x):
                Xtheta(x, i=i, j=j, k=k)


