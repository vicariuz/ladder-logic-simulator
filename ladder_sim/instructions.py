"""Ladder instructions modeled after Rockwell Logix behavior.

All timers work in milliseconds and are updated once per scan with the
scan time (dt). This makes the simulator deterministic and easy to test.
"""


class TON:
    """Timer On-Delay.

    Rung true  -> ACC accumulates; DN turns on when ACC reaches PRE.
    Rung false -> ACC resets to 0 and DN turns off immediately.

    Status bits:
        EN  - rung is true
        TT  - timer is timing (EN and not DN)
        DN  - done (ACC >= PRE)
    """

    def __init__(self, preset_ms: int):
        self.PRE = preset_ms
        self.ACC = 0
        self.EN = self.TT = self.DN = False

    def update(self, rung_in: bool, dt: int) -> bool:
        self.EN = rung_in
        if rung_in:
            self.ACC = min(self.PRE, self.ACC + dt)
            self.DN = self.ACC >= self.PRE
        else:
            self.ACC = 0
            self.DN = False
        self.TT = self.EN and not self.DN
        return self.DN

    def reset(self) -> None:
        self.ACC = 0
        self.EN = self.TT = self.DN = False


class TOF:
    """Timer Off-Delay.

    Rung true  -> DN turns on immediately, ACC = 0.
    Rung false -> ACC accumulates; DN stays on until ACC reaches PRE,
                  then DN turns off.

    Typical use: keep something on for a while after its trigger goes away
    (a fan running after a motor stops, a diverter gate held open, etc.).
    """

    def __init__(self, preset_ms: int):
        self.PRE = preset_ms
        self.ACC = preset_ms          # starts "timed out": DN off at power-up
        self.EN = self.TT = self.DN = False

    def update(self, rung_in: bool, dt: int) -> bool:
        self.EN = rung_in
        if rung_in:
            self.ACC = 0
            self.DN = True
            self.TT = False
        else:
            if self.DN:
                self.ACC = min(self.PRE, self.ACC + dt)
                if self.ACC >= self.PRE:
                    self.DN = False
            self.TT = self.DN       # timing while DN is still on
        return self.DN

    def reset(self) -> None:
        self.ACC = self.PRE
        self.EN = self.TT = self.DN = False


class Counter:
    """Up/Down counter (CTU / CTD share the same counter tag, like Logix).

    Counts on the false->true transition of the rung, not while it stays true.
    DN is on while ACC >= PRE. Use res() for the RES instruction.
    """

    def __init__(self, preset: int):
        self.PRE = preset
        self.ACC = 0
        self.CU = self.CD = self.DN = False

    def ctu(self, rung_in: bool) -> bool:
        if rung_in and not self.CU:
            self.ACC += 1
        self.CU = rung_in
        self.DN = self.ACC >= self.PRE
        return self.DN

    def ctd(self, rung_in: bool) -> bool:
        if rung_in and not self.CD:
            self.ACC -= 1
        self.CD = rung_in
        self.DN = self.ACC >= self.PRE
        return self.DN

    def res(self) -> None:
        self.ACC = 0
        self.DN = False


class OneShot:
    """ONS: true for exactly one scan when the rung goes false -> true."""

    def __init__(self):
        self._storage = False

    def update(self, rung_in: bool) -> bool:
        pulse = rung_in and not self._storage
        self._storage = rung_in
        return pulse


class OneShotFalling:
    """OSF: true for exactly one scan when the rung goes true -> false."""

    def __init__(self):
        self._storage = False

    def update(self, rung_in: bool) -> bool:
        pulse = self._storage and not rung_in
        self._storage = rung_in
        return pulse
