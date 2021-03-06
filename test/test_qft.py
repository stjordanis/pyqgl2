# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

import unittest

# Test functions in multi.py

from pyqgl2.main import compile_function
from pyqgl2.qreg import QRegister
from test.helpers import channel_setup, testable_sequence

from test.helpers import assertPulseSequenceEqual, \
    get_cal_seqs_1qubit, get_cal_seqs_2qubits

from QGL import *

class TestQFT(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_qft(self):
        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        qr = QRegister('q1', 'q2')

        resFunction = compile_function('test/code/qft.py', 'qft', (qr,))
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        # expected_seq = [H(q1), CZ_k(q1, q2, pi), H(q2), MEAS(q1), MEAS(q2)]
        expected_seq = [
            H(q1),
            Ztheta(q2, pi/2),
            CNOT(q1, q2),
            Ztheta(q2, -pi/2),
            CNOT(q1, q2),
            H(q2),
            MEAS(q1),
            MEAS(q2)
        ]
        expected_seq = testable_sequence(expected_seq)

        assertPulseSequenceEqual(self, seqs, expected_seq)

def H(q):
    return [Y90(q), X(q)]
