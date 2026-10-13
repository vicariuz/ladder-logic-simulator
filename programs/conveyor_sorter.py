"""Conveyor that sorts tall parts with a diverter gate and counts a batch.

Layout (parts travel left to right):

    [PE_ENTRY + HEIGHT_SENSOR] ----------> [PE_DIVERT + gate] ---> end
             count + classify                 divert tall parts

Inputs:
    START_PB      - NO push button
    STOP_PB       - NC push button (True when not pressed)
    RESET_PB      - NO push button, resets the batch counters
    PE_ENTRY      - photo-eye at entry, True while a part blocks it
    HEIGHT_SENSOR - True while a TALL part is under it (mounted with PE_ENTRY)
    PE_DIVERT     - photo-eye at the diverter, True while a part blocks it
Outputs:
    MOTOR         - conveyor motor
    DIVERTER      - diverter gate solenoid
    BATCH_DONE    - pilot light, batch of BATCH_SIZE parts completed

The conveyor stops by itself once the batch count is reached AND the last
part has cleared the diverter (so no part is left stranded on the belt).

Instructions used: ONS, CTU, RES, TOF, OSF, latch/unlatch bits.

Simplification: only one part travels between PE_ENTRY and PE_DIVERT at a
time. Tracking several parts at once needs a FIFO / shift register (BSL),
which is a good next exercise.
"""
from ladder_sim import Program, TOF, Counter, OneShot, OneShotFalling


class ConveyorSorter(Program):
    INPUTS = ("START_PB", "STOP_PB", "RESET_PB",
              "PE_ENTRY", "HEIGHT_SENSOR", "PE_DIVERT")
    OUTPUTS = ("MOTOR", "DIVERTER", "BATCH_DONE")
    INPUT_DEFAULTS = {"STOP_PB": True}

    def __init__(self, batch_size=10, gate_hold_ms=800):
        super().__init__()
        self.ONS_ENTRY = OneShot()
        self.OSF_GATE = OneShotFalling()
        self.OSF_EXIT = OneShotFalling()
        self.C_TOTAL = Counter(batch_size)
        self.C_TALL = Counter(batch_size)   # preset unused, used for counting
        self.T_GATE = TOF(gate_hold_ms)
        self.B["TALL_FLAG"] = False
        self.B["PART_IN_ZONE"] = False

    def logic(self, dt):
        I, O, B = self.I, self.O, self.B

        # Rung 0 - RES counters
        if I["RESET_PB"]:
            self.C_TOTAL.res()
            self.C_TALL.res()

        # Rung 1 - batch complete: count reached and belt clear
        batch_complete = (self.C_TOTAL.DN
                          and not B["PART_IN_ZONE"]
                          and not self.T_GATE.DN)

        # Rung 2 - run latch; stops automatically when the batch is complete
        O["MOTOR"] = ((I["START_PB"] or O["MOTOR"])
                      and I["STOP_PB"]
                      and not batch_complete)

        # Rung 3 - one-shot on the leading edge of a part at the entry eye
        entry_pulse = self.ONS_ENTRY.update(I["PE_ENTRY"] and O["MOTOR"])

        # Rung 4 - count every part and mark the zone as occupied
        self.C_TOTAL.ctu(entry_pulse)
        if entry_pulse:
            B["PART_IN_ZONE"] = True

        # Rung 5 - part leaves the diverter eye -> zone is clear again
        if self.OSF_EXIT.update(I["PE_DIVERT"]):
            B["PART_IN_ZONE"] = False

        # Rung 6 - classify: tall part -> latch TALL_FLAG and count it
        tall_entry = entry_pulse and I["HEIGHT_SENSOR"]
        self.C_TALL.ctu(tall_entry)
        if tall_entry:
            B["TALL_FLAG"] = True

        # Rung 7 - open the gate while a tall part is at the diverter, and
        #          hold it open gate_hold_ms after the part clears (TOF)
        self.T_GATE.update(I["PE_DIVERT"] and B["TALL_FLAG"], dt)
        O["DIVERTER"] = self.T_GATE.DN

        # Rung 8 - when the gate closes, clear the tall flag (OSF + OTU)
        if self.OSF_GATE.update(self.T_GATE.DN):
            B["TALL_FLAG"] = False

        # Rung 9 - batch complete light
        O["BATCH_DONE"] = batch_complete
