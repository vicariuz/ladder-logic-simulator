"""Classic 3-wire motor start/stop with seal-in (latch) contact.

Field wiring assumptions (as in real panels):
    START_PB  - normally open push button  (True while pressed)
    STOP_PB   - normally closed push button (True while NOT pressed)
    OL_OK     - overload relay NC contact   (True while no overload)

Rung 0:
    |  START_PB     STOP_PB   OL_OK       MOTOR  |
    |----] [----+----] [-------] [---------( )----|
    |  MOTOR    |                                 |
    |----] [----+                                 |

Because STOP_PB and OL_OK are wired NC, the program uses XIC (] [) on them.
A broken wire therefore stops the motor: this is "fail-safe" design.
"""
from ladder_sim import Program


class MotorStartStop(Program):
    INPUTS = ("START_PB", "STOP_PB", "OL_OK")
    OUTPUTS = ("MOTOR",)
    INPUT_DEFAULTS = {"STOP_PB": True, "OL_OK": True}

    def logic(self, dt):
        I, O = self.I, self.O
        # Rung 0
        O["MOTOR"] = (I["START_PB"] or O["MOTOR"]) and I["STOP_PB"] and I["OL_OK"]
