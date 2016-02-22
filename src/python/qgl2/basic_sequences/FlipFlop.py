# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

from qgl2.qgl2 import qgl2decl, qbit, qgl2main

from QGL.PulsePrimitives import X90, X90m, Y90, Id, X, MEAS
from QGL.Compiler import compile_to_hardware
from QGL.PulseSequencePlotter import plot_pulse_files

from itertools import chain

from .new_helpers import addMeasPulse, compileAndPlot

def FlipFlopq1(qubit: qbit, dragParamSweep, maxNumFFs=10, showPlot=False):
    """
    Flip-flop sequence (X90-X90m)**n to determine off-resonance or DRAG parameter optimization.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    dragParamSweep : drag parameter values to sweep over (iterable)
    maxNumFFs : maximum number of flip-flop pairs to do
    showPlot : whether to plot (boolean)
    """

    # Original:
    # def flipflop_seqs(dragScaling):
    #     """ Helper function to create a list of sequences with a specified drag parameter. """
    #     qubit.pulseParams['dragScaling'] = dragScaling
    #     return [[X90(qubit)] + [X90(qubit), X90m(qubit)]*rep + [Y90(qubit)] for rep in range(maxNumFFs)]

    # # Insert an identity at the start of every set to mark them off
    # originalScaling = qubit.pulseParams['dragScaling']
    # seqs = list(chain.from_iterable([[[Id(qubit)]] + flipflop_seqs(dragParam) for dragParam in dragParamSweep]))
    # qubit.pulseParams['dragScaling'] = originalScaling

    # # Add a final pi for reference
    # seqs.append([X(qubit)])

    # # Add the measurment block to every sequence
    # measBlock = MEAS(qubit)
    # for seq in seqs:
    #     seq.append(measBlock)

    # fileNames = compile_to_hardware(seqs, 'FlipFlop/FlipFlop')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)

    def flipflop_seqs(dragScaling):
        """ Helper function to create a list of sequences with a specified drag parameter. """
        qubit.pulseParams['dragScaling'] = dragScaling
        seqs = []
        for rep in range(maxNumFFs):
            seq = []
            seq.append(X90(qubit))
            # FIXME: Origin used [X90] + [X90, X90m]... is this right?
            for _ in range(rep):
                seq.append(X90(qubit))
                seq.append(X90m(qubit))
            seq.append(Y90(qubit))
            seqs.append(seq)
        return seqs

    # Insert an identity at the start of every set to mark them off
    # Want a result something like:
    # [['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9'], ['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9'], ['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9']]

    seqs = []
    originalScaling = qubit.pulseParams['dragScaling']
    for dragParam in dragParamSweep:
        seqs.append([Id(qubit)])
        # FIXME: In original this was [[Id]] + flipflop - is this
        # right?
        ffs = flipflop_seqs(dragParam)
        for elem in ffs:
            seqs.append(elem)
    qubit.pulseParams['dragScaling'] = originalScaling

    # Add a final pi for reference
    seqs.append([X(qubit)])

    # Add the measurment block to every sequence
    seqs = addMeasPulse(seqs, qubit)

    # Be sure to un-decorate this function to make it work without the
    # QGL2 compiler
    compileAndPlot(seqs, 'FlipFlop/FlipFlop', showPlot)

@qgl2decl
def FlipFlop(qubit: qbit, dragParamSweep, maxNumFFs=10, showPlot=False):
    """
    Flip-flop sequence (X90-X90m)**n to determine off-resonance or DRAG parameter optimization.

    Parameters
    ----------
    qubit : logical channel to implement sequence (LogicalChannel) 
    dragParamSweep : drag parameter values to sweep over (iterable)
    maxNumFFs : maximum number of flip-flop pairs to do
    showPlot : whether to plot (boolean)
    """

    # Original:
    # def flipflop_seqs(dragScaling):
    #     """ Helper function to create a list of sequences with a specified drag parameter. """
    #     qubit.pulseParams['dragScaling'] = dragScaling
    #     return [[X90(qubit)] + [X90(qubit), X90m(qubit)]*rep + [Y90(qubit)] for rep in range(maxNumFFs)]

    # # Insert an identity at the start of every set to mark them off
    # originalScaling = qubit.pulseParams['dragScaling']
    # seqs = list(chain.from_iterable([[[Id(qubit)]] + flipflop_seqs(dragParam) for dragParam in dragParamSweep]))
    # qubit.pulseParams['dragScaling'] = originalScaling

    # # Add a final pi for reference
    # seqs.append([X(qubit)])

    # # Add the measurment block to every sequence
    # measBlock = MEAS(qubit)
    # for seq in seqs:
    #     seq.append(measBlock)

    # fileNames = compile_to_hardware(seqs, 'FlipFlop/FlipFlop')
    # print(fileNames)

    # if showPlot:
    #     plot_pulse_files(fileNames)
    @qgl2decl
    def flipflop_seqs(dragScaling):
        """ Helper function to create a list of sequences with a specified drag parameter. """
        qubit.pulseParams['dragScaling'] = dragScaling
        for rep in range(maxNumFFs):
            X90(qubit)
            # FIXME: Origin used [X90] + [X90, X90m]... is this right?
            for _ in range(rep):
                X90(qubit)
                X90m(qubit)
            Y90(qubit)
            MEAS(qubit) # FIXME: Need original dragScaling?

    # Insert an identity at the start of every set to mark them off
    # Want a result something like:
    # [['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9'], ['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9'], ['Id'], ['X9', 'Y9'], ['X9', 'X9', 'X9m', 'Y9'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9']]

    originalScaling = qubit.pulseParams['dragScaling']
    for dragParam in dragParamSweep:
        Id(qubit)
        MEAS(qubit) # FIXME: Need original dragScaling?

        # FIXME: In original this was [[Id]] + flipflop - is this
        # right?
        flipflop_seqs(dragParam)
    qubit.pulseParams['dragScaling'] = originalScaling

    # Add a final pi for reference
    X(qubit)
    MEAS(qubit)

    # Final result is something like this:
    # [['Id', 'M'], ['X9', 'Y9', 'M'], ['X9', 'X9', 'X9m', 'Y9', 'M'],
    # ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9', 'M'], ['Id', 'M'], ['X9',
    # 'Y9', 'M'], ['X9', 'X9', 'X9m', 'Y9', 'M'], ['X9', 'X9', 'X9m',
    # 'X9', 'X9m', 'Y9', 'M'], ['Id', 'M'], ['X9', 'Y9', 'M'], ['X9',
    # 'X9', 'X9m', 'Y9', 'M'], ['X9', 'X9', 'X9m', 'X9', 'X9m', 'Y9',
    # 'M'], ['X', 'M']]

    # Here we rely on the QGL compiler to pass in the sequence it
    # generates to compileAndPlot
    compileAndPlot('FlipFlop/FlipFlop', showPlot)

# Imports for testing only
from qgl2.qgl2 import Qbit
from QGL.Channels import Qubit, LogicalMarkerChannel
import numpy as np
from math import pi

@qgl2main
def main():
    # Set up 1 qbit, following model in QGL/test/test_Sequences

    # FIXME: Cannot use these in current QGL2 compiler, because
    # a: QGL2 doesn't understand creating class instances, and 
    # b: QGL2 currently only understands the fake Qbits
#    qg1 = LogicalMarkerChannel(label="q1-gate")
#    q1 = Qubit(label='q1', gateChan=qg1)
#    q1.pulseParams['length'] = 30e-9
#    q1.pulseParams['phase'] = pi/2

    # But the current qgl2 compiler doesn't understand Qubits, only
    # Qbits. So use that instead when running through the QGL2
    # compiler, but comment this out when running directly.
    q1 = Qbit(1)
    FlipFlop(q1, np.linspace(0, 5e-6, 11))

