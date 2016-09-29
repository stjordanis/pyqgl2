# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 versions of Rabi.py functions.
# These work around QGL2 constraints, such as only doing sequence generation and
# not compilation, or not taking arguments.

from qgl2.qgl2 import qgl2decl, qbit, concur
from qgl2.qgl1 import QubitFactory, Utheta, MEAS, X, Id
from qgl2.util import init

import qgl2.basic_sequences.pulses

from qgl2.basic_sequences.helpers import create_cal_seqs

import numpy as np

@qgl2decl
def doRabiWidth(q:qbit, widths):
    # FIXME: Note the local re-definition of tanh
    shapeFun = qgl2.basic_sequences.pulses.local_tanh
    for l in widths:
        init(q)
        Utheta(q, length=l, amp=1, phase=0, shapeFun=shapeFun)
        MEAS(q)

@qgl2decl
def doRabiAmp(q:qbit, amps, phase):
    for amp in amps:
        init(q)
        Utheta(q, amp=amp, phase=phase)
        MEAS(q)

@qgl2decl
def doRabiAmpPi(q1:qbit, q2:qbit, amps):
    for l in amps:
        with concur:
            init(q1)
            init(q2)
        X(q2)
        Utheta(q1, amp=l, phase=0)
        X(q2)
        MEAS(q2)

@qgl2decl
def doSingleShot(q:qbit):
    init(q)
    Id(q)
    MEAS(q)
    init(q)
    X(q)
    MEAS(q)

@qgl2decl
def doPulsedSpec(q:qbit, specOn):
    init(q)
    if specOn:
        X(q)
    else:
        Id(q)
    MEAS(q)

# Rabi_Amp_NQubits in QGL1 has a bug; it should
# be doing MEAS over the measChans. So something like below.

@qgl2decl
def doRabiAmp_NQubits(amps, docals, calRepeats):
    # FIXME: want to pass q1 and q2 as a qbit_list arg
    q1 = QubitFactory('q1')
    q2 = QubitFactory('q2')
    qubits = [q1, q2]
    p = 0

    for a in amps:
        with concur:
            for q in qubits:
                init(q)
                Utheta(q, amp=a, phase=p)
                MEAS(q)

    if docals:
        create_cal_seqs(qubits, calRepeats)

# This version allows the Xs and Id pulse to be done in parallel,
# as quick as possible. But we can't tell what the QGL1 method was
# trying to do, so this may be meaningless.
@qgl2decl
def doSwap(q:qbit, mq:qbit, delays):

    for d in delays:
        with concur:
            init(q)
            init(mq)
            X(q)
            X(mq)
            Id(mq, length=d)
        with concur:
            MEAS(mq)
            MEAS(q)

    create_cal_seqs((mq, q), 2)
