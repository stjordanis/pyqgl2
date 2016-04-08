# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list, concur, pulse

from .qgl2_plumbing import init

from functools import reduce
from itertools import product
import operator

from QGL.PulsePrimitives import Id, X, MEAS
from QGL.ControlFlow import qwait

@qgl2decl
def create_cal_seqs(qubits: qbit_list, numRepeats, measChans: qbit_list = None, waitcmp=False) -> pulse:
    """
    Helper function to create a set of calibration sequences.

    Parameters
    ----------
    qubits : logical channels, e.g. (q1,) or (q1,q2) (tuple) 
    numRepeats = number of times to repeat calibration sequences (int)
    waitcmp = True if the sequence contains branching
    """
    # Make all combinations for qubit calibration states for n qubits and repeat

    # Assuming numRepeats=2 and qubits are q1, q2 and waitCmp=False, 
    # Produces 2 ^ #qubits * numRepeats sequences of Id, X, MEAS, 
    # something like
    # [[Id(q1)*Id(q2), M(q1)*M(q2)], [Id(q1)*Id(q2), M(q1)*M(q2)],
    #  [Id(q1)*X(q2), M(q1)*M(q2)],  [Id(q1)*X(q2), M(q1)*M(q2)],
    #  [X(q1)*Id(q2), M(q1)*M(q2)],  [X(q1)*Id(q2), M(q1)*M(q2)],
    #  [X(q1)*X(q2), M(q1)*M(q2)],   [X(q1)*X(q2), M(q1)*M(q2)]]

    # Original:
    # calSeqs = [reduce(operator.mul, [p(q) for p,q in zip(pulseSet, qubits)]) for pulseSet in product(calSet, repeat=len(qubits)) for _ in range(numRepeats)]
    # return [[seq, MEAS(*measChans), qwait('CMP')] if waitcmp else [seq, MEAS(*measChans)] for seq in calSeqs] 

    if measChans is None:
        measChans = qubits

    # Calibrate using Id and X pulses
    calSet = [Id, X]

    # For QGL1
#    calSeqs = []

    # Create iterator with the right number of Id and X pulses
    for pulseSet in product(calSet, repeat=len(qubits)):
        # Repeat each entry numRepeats times
        for _ in range(numRepeats):
            # then do each pulse on each qubit concurrently

            # For QGL1
#            seqs = []
#            # Get all combinations of the pulses and qubits
#            # doing the pulse on the qubit
#            for pulse,qubit in zip(pulseSet, qubits):
#                seqs.append(pulse(qubit))
#            # Do the pulses concurrently for this pulseSet
#            calSeqs.append(reduce(operator.mul, seqs))

            # For QGL2
            # Initialize each sequence / experiment
            with concur:
                for q in qubits:
                    init(q)
            # Get all combinations of the pulses and qubits
            # doing the pulse on the qubit
            # Do the pulses concurrently for this pulseSet
            with concur:
                for pulse,qubit in zip(pulseSet, qubits):
                    pulse(qubit)
            # Add on the measurement pulses (done concurrently)
            with concur:
                for chan in measChans:
                    MEAS(chan)
            # Optionally wait here
            if waitcmp:
                qwait('CMP') # How will QGL2 do with this ControlInstruction?

    # QGL1 only here:
#    # Add on the measurement operator, optionally waiting
#    newCalSeqs = []
#    for seq in calSeqs:
#        if waitcmp:
#            newCalSeqs.append([seq, MEAS(*tuple(measChans)), qwait('CMP')])
#        else:
#            newCalSeqs.append([seq, MEAS(*tuple(measChans))])
#    return newCalSeqs

    # FIXME: QGL2 must return the generated sequences!
#    return []
