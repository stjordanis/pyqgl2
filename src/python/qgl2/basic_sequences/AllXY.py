# Copyright 2016 by Raytheon BBN Technologies Corp.  All Rights Reserved.

# QGL2 simplified versions of AllXY

from qgl2.qgl2 import qgl2main, qgl2decl, qreg, QRegister
from qgl2.util import init

from qgl2.qgl1 import Id, X, Y, X90, Y90, MEAS

@qgl2decl
def AllXY(q: qreg):
    # QGL2 version of QGL2 Basic Sequence
    # Must be compiled & given a QRegister
    # 6/12/19: Verified this looks same as QGL1 version
    
    twentyOnePulsePairs = [
            # no pulses to measure |0>
            (Id, Id),
            # pulse around same axis
            (X, X), (Y, Y),
            # pulse around orthogonal axes
            (X, Y), (Y, X),
            # These produce a |+> or |i> state
            (X90, Id), (Y90, Id),
            # pulse pairs around orthogonal axes with 1e error sensititivity
            (X90, Y90), (Y90, X90),
            # pulse pairs with 2e sensitivity
            (X90, Y), (Y90, X), (X, Y90), (Y, X90),
            # pulse pairs around common axis with 3e error sensitivity
            (X90, X), (X, X90), (Y90, Y), (Y, Y90),
            # These create the |1> state
            (X, Id), (Y, Id),
            (X90, X90), (Y90, Y90) ]

    # For each of the 21 pulse pairs
    for (f1, f2) in twentyOnePulsePairs:
        # Repeat it twice and do a MEAS at the end of each
        for i in range(2):
            init(q)
            f1(q)
            f2(q)
            MEAS(q)


@qgl2decl
def doAllXY():
    # All in one QGL2 function to avoid args
    from qgl2.qgl2 import QRegister
    q = QRegister('q1')
    AllXY(q)

# QGL1 function to compile the above QGL2
# Uses main.py
# FIXME: Use the same argument parsing
def main():
    from pyqgl2.qreg import QRegister
    import pyqgl2.test_cl
    from pyqgl2.main import compile_function, qgl2_compile_to_hardware
    
    toHW = False
    plotPulses = False
    pyqgl2.test_cl.create_default_channelLibrary(toHW, True)
    
#    # To turn on verbose logging in compile_function
#    from pyqgl2.ast_util import NodeError
#    from pyqgl2.debugmsg import DebugMsg
#    NodeError.MUTE_ERR_LEVEL = NodeError.NODE_ERROR_NONE
#    DebugMsg.set_level(0)
    
    # Now compile the QGL2 to produce the function that would generate the expected sequence.
    # Supply the path to the QGL2, the main function in that file, and a list of the args to that function.
    # Can optionally supply saveOutput=True to save the qgl1.py
    # file,
    # and intermediate_output="path-to-output-file" to save
    # intermediate products

    # Pass in a QRegister NOT the real Qubit
    q = QRegister(1)
    resFunction = compile_function("src/python/qgl2/basic_sequences/AllXYMin.py",
                                               "AllXY",
                                               (q,))
    # Run the QGL2. Note that the generated function takes no arguments itself
    sequences = resFunction()
    if toHW:
        print("Compiling sequences to hardware\n")
        # file prefix AllXY/AllXY, no suffix
        fileNames = qgl2_compile_to_hardware(sequences, 'AllXY/AllXY')
        print(fileNames)
        if plotPulses:
            from QGL.PulseSequencePlotter import plot_pulse_files
            plot_pulse_files(fileNames)
    else:
        print("\nGenerated sequences:\n")
        from QGL.Scheduler import schedule
        
        scheduled_seq = schedule(sequences)
        from IPython.lib.pretty import pretty
        print(pretty(scheduled_seq))

if __name__ == "__main__":
    # I'd like to call pyqgl2.main but with particular args
    # if -toHW or -showplot, pass those on
    # to run a basic sequence, run
    # basic_sequences/filename.py -m doTestname [-toHW [-showplt]]
    # pyqgl2.main.__main__(sys.argv[1:]
    main()
