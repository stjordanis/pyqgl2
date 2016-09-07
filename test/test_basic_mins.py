import unittest
import numpy as np

from pyqgl2.main import compileFunction
from QGL import *

from .helpers import channel_setup, testable_sequence

class TestBasicMins(unittest.TestCase):
    def setUp(self):
        channel_setup()

    def tearDown(self):
        pass

    def test_RabiAmp(self):
        q1 = QubitFactory('q1')
        expectedseq = []
        for amp in np.linspace(0, 1, 11):
            expectedseq += [
                qsync(),
                qwait(),
                Utheta(q1, amp=amp),
                MEAS(q1)
            ]

        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmp")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.assertEqual(seqs[0], expectedseq)

        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmp3")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.assertEqual(seqs[0], expectedseq)

        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmp4")
        seqs = resFunction()
        seqs = testable_sequence(seqs)
        self.assertEqual(seqs[0], expectedseq)

    @unittest.expectedFailure
    def test_RabiWidth(self):
        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiWidth")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        q1 = QubitFactory('q1')
        expectedseq = []
        for l in np.linspace(0, 5e-6, 11):
            expectedseq += [
                qsync(),
                qwait(),
                Utheta(q1, length=l, amp=1, phase=0, shapeFun=PulseShapes.tanh),
                MEAS(q1)
            ]

        self.assertEqual(seqs[0], expectedseq)

    def test_RabiAmpPi(self):
        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doRabiAmpPi")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        q1 = QubitFactory('q1')
        q2 = QubitFactory('q2')
        expectedseq1 = []
        expectedseq2 = []
        for amp in np.linspace(0, 1, 11):
            expectedseq1 += [
                qsync(),
                qwait(),
                Id(q1, length=X(q2).length), # fills space of X(q2)
                Utheta(q1, amp=amp, phase=0),
                Id(q1, length=X(q2).length), # fills space of X(q2)
                Id(q1, length=MEAS(q2).length) # fills space of MEAS(q2)
            ]
            expectedseq2 += [
                qsync(),
                qwait(),
                X(q2),
                Id(q2, length=X(q1).length), # fills space of Utheta(q1)
                X(q2),
                MEAS(q2)
            ]

        self.assertEqual(seqs[0], expectedseq1)
        self.assertEqual(seqs[1], expectedseq2)

    def test_SingleShot(self):
        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doSingleShot")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        q1 = QubitFactory('q1')
        expectedseq = [
            qsync(),
            qwait(),
            Id(q1),
            MEAS(q1),
            qsync(),
            qwait(),
            X(q1),
            MEAS(q1)
        ]

        self.assertEqual(seqs[0], expectedseq)

    def test_PulsedSpec(self):
        resFunction = compileFunction("src/python/qgl2/basic_sequences/RabiMin.py",
                                      "doPulsedSpec")
        seqs = resFunction()
        seqs = testable_sequence(seqs)

        q1 = QubitFactory('q1')
        expectedseq = [
            qsync(),
            qwait(),
            X(q1),
            MEAS(q1)
        ]

        self.assertEqual(seqs[0], expectedseq)
