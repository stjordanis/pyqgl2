# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, concur, qbit_list
from qgl2.util import init
from qgl2.qgl1 import Id, flat_top_gaussian_edge, X, QubitFactory, \
    X90, echoCR
from qgl2.qgl1 import MEAS
from qgl2.basic_sequences.helpers import create_cal_seqs

import numpy as np
from math import pi

@qgl2decl
def meas_all(qubits: qbit_list):
    for q in qubits:
        MEAS(q)

@qgl2decl
def doPiRabi():
    # FIXME: No arguments allowed
    controlQ = QubitFactory('q1')
    targetQ = QubitFactory('q2')
    # FIXME: Better values!?
    lengths = np.linspace(0, 4e-6, 11)
    riseFall=40e-9
    amp=1
    phase=0
    calRepeats=2

    # Sequence 1: Id(control), gaussian(l), measure both
    for l in lengths:
        init(controlQ)
        init(targetQ)
        Id(controlQ)
        flat_top_gaussian_edge(controlQ, targetQ, riseFall, amp=amp, phase=phase, length=l)
        Barrier("", (targetQ, controlQ))
        meas_all([targetQ, controlQ])

    # Sequence 2: X(control), gaussian(l), X(control), measure both
    for l in lengths:
        init(controlQ)
        init(targetQ)
        X(controlQ)
        flat_top_gaussian_edge(controlQ, targetQ, riseFall, amp=amp, phase=phase, length=l)
        X(controlQ)
        Barrier("", (targetQ, controlQ))
        meas_all([targetQ, controlQ])

    # Then do calRepeats calibration sequences
    create_cal_seqs((targetQ, controlQ), calRepeats)

@qgl2decl
def doEchoCRLen():
    # FIXME: No arguments allowed
    controlQ = QubitFactory('q1')
    targetQ = QubitFactory('q2')
    # FIXME: Better values!?
    lengths = np.linspace(0, 2e-6, 11)
    riseFall=40e-9
    amp=1
    phase=0
    calRepeats=2

    # Sequence1:
    for l in lengths:
        init(controlQ)
        init(targetQ)
        Id(controlQ)
        echoCR(controlQ, targetQ, length=l, phase=phase,
               riseFall=riseFall)
        Id(controlQ)
        Barrier("", (targetQ, controlQ))
        meas_all([targetQ, controlQ])

    # Sequence 2
    for l in lengths:
        init(controlQ)
        init(targetQ)
        X(controlQ)
        echoCR(controlQ, targetQ, length=l, phase=phase,
               riseFall=riseFall)
        X(controlQ)
        Barrier("", (targetQ, controlQ))
        meas_all([targetQ, controlQ])

    # Then do calRepeats calibration sequences
    create_cal_seqs((targetQ, controlQ), calRepeats)

@qgl2decl
def doEchoCRPhase():
    # FIXME: No arguments allowed
    controlQ = QubitFactory('q1')
    targetQ = QubitFactory('q2')
    # FIXME: Better values!?
    phases = np.linspace(0, pi/2, 11)
    riseFall=40e-9
    amp=1
    length=100e-9
    calRepeats=2

    # Sequence 1
    for ph in phases:
        init(controlQ)
        init(targetQ)
        Id(controlQ)
        echoCR(controlQ, targetQ, length=length, phase=ph,
               riseFall=riseFall)
        X90(targetQ)
        Id(controlQ)
        Barrier("", (targetQ, controlQ))
        meas_all([targetQ, controlQ])

    # Sequence 2
    for ph in phases:
        init(controlQ)
        init(targetQ)
        X(controlQ)
        echoCR(controlQ, targetQ, length=length, phase=ph,
               riseFall=riseFall)
        X90(targetQ)
        X(controlQ)
        Barrier("", (targetQ, controlQ))
        meas_all([targetQ, controlQ])

    # Then do calRepeats calibration sequences
    create_cal_seqs((targetQ, controlQ), calRepeats)
