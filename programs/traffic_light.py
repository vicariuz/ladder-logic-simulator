"""Traffic light with cascaded TON timers (a classic training exercise).

Sequence: GREEN 5 s -> YELLOW 2 s -> RED 5 s -> repeat, while RUN is on.
When RUN is off, only RED is on.

Rung 0:  |  RUN    T_RED.DN                 T_GREEN    |
         |--] [-----]/[------------------[TON 5000]----|
Rung 1:  |  T_GREEN.DN                      T_YELLOW   |
         |--] [--------------------------[TON 2000]----|
Rung 2:  |  T_YELLOW.DN                     T_RED      |
         |--] [--------------------------[TON 5000]----|
Rung 3:  |  RUN    T_GREEN.DN               GREEN      |
         |--] [-----]/[----------------------( )-------|
Rung 4:  |  T_GREEN.DN  T_YELLOW.DN          YELLOW    |
         |--] [----------]/[-----------------( )-------|
Rung 5:  |  RUN                               RED      |
         |--]/[--------------+---------------( )-------|
         |  T_YELLOW.DN      |                         |
         |--] [--------------+                         |

When T_RED finishes, its DN bit opens rung 0 on the next scan. T_GREEN
resets, which resets T_YELLOW, which resets T_RED: the cycle restarts.
"""
from ladder_sim import Program, TON


class TrafficLight(Program):
    INPUTS = ("RUN",)
    OUTPUTS = ("GREEN", "YELLOW", "RED")

    def __init__(self, green_ms=5000, yellow_ms=2000, red_ms=5000):
        super().__init__()
        self.T_GREEN = TON(green_ms)
        self.T_YELLOW = TON(yellow_ms)
        self.T_RED = TON(red_ms)

    def logic(self, dt):
        I, O = self.I, self.O
        self.T_GREEN.update(I["RUN"] and not self.T_RED.DN, dt)   # Rung 0
        self.T_YELLOW.update(self.T_GREEN.DN, dt)                 # Rung 1
        self.T_RED.update(self.T_YELLOW.DN, dt)                   # Rung 2
        O["GREEN"] = I["RUN"] and not self.T_GREEN.DN             # Rung 3
        O["YELLOW"] = self.T_GREEN.DN and not self.T_YELLOW.DN    # Rung 4
        O["RED"] = (not I["RUN"]) or self.T_YELLOW.DN             # Rung 5
