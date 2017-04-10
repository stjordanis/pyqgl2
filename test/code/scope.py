from qgl2.qgl2 import concur, qgl2decl
from qgl2.qgl2 import qbit, qbit_list
from qgl2.qgl1 import QubitFactory, Xtheta, Ytheta

@qgl2decl
def A(q: qbit):
    a = 1
    Xtheta(q, amp=a)

@qgl2decl
def B():
    # this test tries to refer to a variable defined within A
    # it should produce an error because 'a' is not defined in the
    # scope of B()
    q = QubitFactory("q1")
    A(q)
    Ytheta(q, amp=a)

@qgl2decl
def C():
    # this test checks whether the 'a' refered to in A() clobbers the 'a'
    # which is in scope of C().
    q = QubitFactory("q1")
    a = 0
    A(q)
    Ytheta(q, amp=a)