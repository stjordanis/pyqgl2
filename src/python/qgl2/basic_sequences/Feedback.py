# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit_list

from QGL.PulsePrimitives import Id, MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files
from QGL.ControlFlow import qif, qwait

from .helpers import create_cal_seqs

from functools import reduce
from itertools import product
import operator

# Note that measChans should have a default value that is identical to qubits
@qgl2decl
def Reset(qubits: qbit_list, measDelay = 1e-6, signVec = None,
          doubleRound = True, buf = 30e-9, showPlot=False, measChans: qbit_list = None, docals=True, calRepeats=2):
    """

    Variable amplitude Rabi nutation experiment for an arbitrary number of qubits simultaneously

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    measDelay : delay between end of measuerement and LOADCMP
    signVec : conditions for feedback. List of 0 (flip if signal is above threshold) and 1 (flip if below) for each qubit. Default = 0 for all qubits
    doubleRound : if true, double round of feedback
    showPlot : whether to plot (boolean)
    measChans : tuble of qubits to be measured (LogicalChannel)
    docals, calRepeats: enable calibration sequences, repeated calRepeats times
    """

    # Original:
    # if measChans is None:
    #     measChans = qubits

    # if signVec == None:
    #     signVec = [0]*len(qubits)

    # states = create_cal_seqs(qubits,1,measChans=measChans)
    # FbSet = [Id, X]
    # FbSet2 = [X, Id]
    # FbGates = []

    # for count in range(len(qubits)):
    #     FbGates += [FbSet] if signVec[count]==0 else [FbSet2]
    # FbSeq = [reduce(operator.mul, [p(q) for p,q in zip(pulseSet, qubits)]) for pulseSet in product(*FbGates)]
    # seqs = [state + [MEAS(*measChans), Id(qubits[0],measDelay), qwait('CMP'), Id(qubits[0],buf)] + [branch for b in [qif(fbcount,[FbSeq[count]]) for fbcount in range(len(states))] for branch in b] + [MEAS(*measChans)] for count, state in enumerate(states)]

    # if doubleRound:
    #     seqs = [seq + [Id(qubits[0],measDelay), qwait('CMP'), Id(qubits[0],buf)] + [branch for b in [qif(fbcount,[FbSeq[count]]) for fbcount in range(2**len(qubits))] for branch in b] + [MEAS(*measChans)] for seq in seqs]
    # print(seqs[0])
    # if docals:
    #     seqs += create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # fileNames = compile_to_hardware(seqs, 'Reset/Reset')

    # if showPlot:
    #     plot_pulse_files(fileNames)


    # signVec determines the order that the product(Id, X) sets end up
    # in
    # That is, the product() thing means we'll do all combos of Id,X
    # for each qubit, but we vary the order of those
    raise NotImplementedError("Reset for QGL2 Not implemented")

# Note that measChans should have a default value that is identical to qubits
def Resetq1(qubits: qbit_list, measDelay = 1e-6, signVec = None,
          doubleRound = True, buf = 30e-9, showPlot=False, measChans: qbit_list = None, docals=True, calRepeats=2):
    """

    Variable amplitude Rabi nutation experiment for an arbitrary number of qubits simultaneously

    Parameters
    ----------
    qubits : tuple of logical channels to implement sequence (LogicalChannel)
    measDelay : delay between end of measuerement and LOADCMP
    signVec : conditions for feedback. List of 0 (flip if signal is above threshold) and 1 (flip if below) for each qubit. Default = 0 for all qubits
    doubleRound : if true, double round of feedback
    showPlot : whether to plot (boolean)
    measChans : tuble of qubits to be measured (LogicalChannel)
    docals, calRepeats: enable calibration sequences, repeated calRepeats times
    """

    # This will produce 2^numQubits sequences, such that in each
    # sequence we try a different combination of the bits in the
    # comparison register.
    # Each sequence does some calibration like pulses, measurements,
    # then a bunch of qifs with all the possible different masks, then
    # measure again.
    # And if doubleRound is set, do it again.

    # Note that the if clause to the qif depends on the sign of the
    # qubit: Default is ID, X like in calibration sequences.

    # Original:
    # if measChans is None:
    #     measChans = qubits

    # if signVec == None:
    #     signVec = [0]*len(qubits)

    # states = create_cal_seqs(qubits,1,measChans=measChans)
    # FbSet = [Id, X]
    # FbSet2 = [X, Id]
    # FbGates = []

    # for count in range(len(qubits)):
    #     FbGates += [FbSet] if signVec[count]==0 else [FbSet2]
    # FbSeq = [reduce(operator.mul, [p(q) for p,q in zip(pulseSet, qubits)]) for pulseSet in product(*FbGates)]
    # seqs = [state + [MEAS(*measChans), Id(qubits[0],measDelay), qwait('CMP'), Id(qubits[0],buf)] + [branch for b in [qif(fbcount,[FbSeq[count]]) for fbcount in range(len(states))] for branch in b] + [MEAS(*measChans)] for count, state in enumerate(states)]

    # if doubleRound:
    #     seqs = [seq + [Id(qubits[0],measDelay), qwait('CMP'), Id(qubits[0],buf)] + [branch for b in [qif(fbcount,[FbSeq[count]]) for fbcount in range(2**len(qubits))] for branch in b] + [MEAS(*measChans)] for seq in seqs]
    # print(seqs[0])
    # if docals:
    #     seqs += create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # fileNames = compile_to_hardware(seqs, 'Reset/Reset')

    # if showPlot:
    #     plot_pulse_files(fileNames)


    # signVec determines the order that the product(Id, X) sets end up
    # in
    # That is, the product() thing means we'll do all combos of Id,X
    # for each qubit, but we vary the order of those

    if measChans is None:
        measChans = qubits

    # Calibrate sequence for the qubits - there will be 2^len(qubits)
    # states
    # Note that the calibration sequence is the un-inverted entry in
    # FbGates below, and there are as many calibration sequences as
    # there are entries in FbSeq
    # Each sequence in the final result will start with one of these
    # calibration sequences
    calSeqs = create_cal_seqs(qubits,1,measChans=measChans)


    # This next block creates something called FbSeq. This is like
    # calSeqs, except that for some qubits the "calibration sequence"
    # is inverted (X, ID).
    # Each of these becomes the if pulse in the qif() clauses in each
    # sequence in the final result.
    # There will be 2^numQubits of these - 1 per final sequence

    # Default signVec to 0 for all qubits
    if signVec == None:
        signVec = [0]*len(qubits)

    # Collect the gates in 1 sequence
    FbGates = []

    # Sometimes state assignments are 'flipped'. Hence this code.
    # Create the FbGates sequences: Each of 2 gates per qubit, based on the
    # signVec
    # Note that QGL2 does not yet handle this kind of function reference
    for count in range(len(qubits)):
        if signVec[count] == 0:
            FbGates += [[Id, X]] # This is the order used in calibration
        else:
            FbGates += [[X, Id]] # This is inverted

    # This will be a sequence of concurrent pulses (in each, 1 per
    # qubit)
    # of length 2^# qubits
    # This is used as the If clause of the qifs below
    # So one of these per sequence in the final result
    FbSeq = []

    # Each set is length of # of qubits
    # But this is full set of combinations of Id and X in the order
    # determined by signVec
    for pulseSet in product(*FbGates):
        # Each entry is concurrently doing a pulse on each qubit
        allPulsePairs = []
        for pulse, qubit in zip(pulseSet, qubits):
            allPulsePairs.append(pulse(qubit))
        FbSeq.append(
            reduce(operator.mul, allPulsePairs)
        )

    # FbSeq is now a sequence of concurrent pulses (in each, Id
    # or X per qubit), of length 2^# qubits
    # EG for 2 qubits of opposite signVec, it gives:
    # [Id(q1)*X(q2), Id(q1)*Id(q2), X(q1)*X(q2), X(q1)*Id(q2)]

    # FbSeq is of same length as calSeqs: 2^#qubits, and made of
    # similar pulses - though the calibration sequences include MEAS pulses

    # seqs is the final result list of sequences
    seqs = []
    # For each calibrate sequence create an element in seqs
    # calSeq is aka state - but why?
    for count, calSeq in enumerate(calSeqs):
        # qifs: for each calibrate there's a qif using that index as the
        # mask, with the test (if clause) being the matching pulse in FbSeq for
        # this calibrate sequence
        # Put another way, we call qif on every mask from 1 to
        # 2^numQubits, each time using the Pulse from FbSeq for this
        # sequence / calibration sequence in the final result.

        # Note a qif is a sequence of pulses, really
        qElse = [FbSeq[count]]
        qifs = []
        for fbcount in range(2**len(qubits)):
            qifs.append(qif(fbcount, qElse))

        # Tease apart the pieces of the qifs and add those all to a
        # new branches sequence. That is, turn [[1, 2, 3], [4, 5, 6]]
        # into [1, 2, 3, 4, 5, 6]
        branches = []
        # qifInstance aka b
        for qifInstance in qifs:
            for branch in qifInstance:
                branches.append(branch)

        # Now create the sequence
        seqs.append(
            calSeq +
            [
                MEAS(*measChans),
                Id(qubits[0],measDelay),
                qwait('CMP'),
                Id(qubits[0],buf)
            ] +
            branches +
            [MEAS(*measChans)]
        )

    # if doubleRound:
    #     seqs = [seq + [Id(qubits[0],measDelay), qwait('CMP'), Id(qubits[0],buf)] + [branch for b in [qif(fbcount,[FbSeq[count]]) for fbcount in range(2**len(qubits))] for branch in b] + [MEAS(*measChans)] for seq in seqs]
    # print(seqs[0])

    # If doubling, add to each sequence Id, qwait, Id, a bunch of
    # qifs, and some concurrent MEAS calls
    # That is, roughly double each sequence, but skip the initial MEAS
    # and the qifs all use a single if clause.
    if doubleRound:
        # FIXME: This 'count' is just the last count from the last
        # calibrate sequence? Really? Seems arbitrary whether this is
        # IdX or XId - does it not matter?
        # Other than that, the qifs created here are idential to the
        # last set of qifs created above
        qElse = [FbSeq[count]]

        qifs = []
        for fbcount in range(2**len(qubits)):
            qifs.append(qif(fbcount, qElse))

        # Tease apart the pieces of the qifs and add those all to a
        # new branches sequence, flattening a list of lists into a
        # single list
        branches = []
        # qifInstance aka b
        for qifInstance in qifs:
            for branch in qifInstance:
                branches.append(branch)

        # Now add the new pulses to each sequence - not just the last one
        for seq in seqs:
            seq.append(
                    [
                        Id(qubits[0], measDelay),
                        qwait('CMP'),
                        Id(qubits[0], buf)
                    ] +
                    branches +
                    [MEAS(*measChans)]
                )

    # If we're doing calibration too, add that at the very end
    # - another 2^numQubits * calRepeats sequences
    if docals:
        seqs += create_cal_seqs(qubits, calRepeats, measChans=measChans)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'Reset/Reset', showPlot)

