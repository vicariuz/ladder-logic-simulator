"""ladder_sim: a small, educational PLC ladder logic simulator.

Instructions are modeled after Rockwell Logix (Studio 5000) so that what you
practice here maps directly to real controllers: TON / TOF timers with
.PRE / .ACC / .EN / .TT / .DN, CTU / CTD counters with .PRE / .ACC / .DN,
and one-shots (ONS / OSF).
"""
from .instructions import TON, TOF, Counter, OneShot, OneShotFalling
from .core import Program, PLCSimulator

__all__ = ["TON", "TOF", "Counter", "OneShot", "OneShotFalling",
           "Program", "PLCSimulator"]
