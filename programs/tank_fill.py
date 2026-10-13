"""Tank level control with hysteresis, high-high alarm and fill timeout.

Inputs:
    START_PB   - NO push button
    STOP_PB    - NC push button (True when not pressed)
    RESET_PB   - NO push button, clears a latched fault
    LS_LOW     - level switch, True when liquid is ABOVE the low point
    LS_HIGH    - level switch, True when liquid is AT/ABOVE the high point
    LS_HH      - high-high (overflow) switch, True when tank is overfull
Outputs:
    SYSTEM_ON  - system running pilot light
    FILL_VALVE - inlet valve solenoid
    ALARM      - alarm horn/light (high-high or fill timeout)

How it works:
    * Filling starts when level drops below LS_LOW and stops at LS_HIGH.
      The gap between the two switches (hysteresis) prevents the valve from
      chattering on and off.
    * If the valve has been open for FILL_TIMEOUT ms without reaching LS_HIGH,
      something is wrong (stuck valve, failed sensor, no supply). A fault is
      latched and filling stops until RESET_PB is pressed. This is exactly the
      kind of logic a technician sees when troubleshooting a "fill timeout"
      alarm on a real machine.

Rung 0  SYSTEM_ON  = (START_PB or SYSTEM_ON) and STOP_PB
Rung 1  FILL_VALVE = SYSTEM_ON and (not LS_LOW or FILL_VALVE)
                     and not LS_HIGH and not LS_HH and not FAULT
Rung 2  T_FILL     = TON(FILL_VALVE)
Rung 3  FAULT      = OTL when T_FILL.DN ; OTU when RESET_PB
Rung 4  ALARM      = LS_HH or FAULT
"""
from ladder_sim import Program, TON


class TankFill(Program):
    INPUTS = ("START_PB", "STOP_PB", "RESET_PB", "LS_LOW", "LS_HIGH", "LS_HH")
    OUTPUTS = ("SYSTEM_ON", "FILL_VALVE", "ALARM")
    INPUT_DEFAULTS = {"STOP_PB": True}

    def __init__(self, fill_timeout_ms=30_000):
        super().__init__()
        self.T_FILL = TON(fill_timeout_ms)
        self.B["FAULT"] = False

    def logic(self, dt):
        I, O, B = self.I, self.O, self.B
        # Rung 0 - system on/off with seal-in
        O["SYSTEM_ON"] = (I["START_PB"] or O["SYSTEM_ON"]) and I["STOP_PB"]
        # Rung 1 - fill valve with hysteresis between LS_LOW and LS_HIGH
        O["FILL_VALVE"] = (O["SYSTEM_ON"]
                           and ((not I["LS_LOW"]) or O["FILL_VALVE"])
                           and not I["LS_HIGH"]
                           and not I["LS_HH"]
                           and not B["FAULT"])
        # Rung 2 - fill timeout timer
        self.T_FILL.update(O["FILL_VALVE"], dt)
        # Rung 3 - latch / unlatch fault (OTL / OTU)
        if self.T_FILL.DN:
            B["FAULT"] = True
        if I["RESET_PB"]:
            B["FAULT"] = False
        # Rung 4 - alarm
        O["ALARM"] = I["LS_HH"] or B["FAULT"]
