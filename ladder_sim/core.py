"""Scan-cycle engine.

A real PLC repeats three steps forever:
    1. Read inputs   - copy field inputs into the input image table
    2. Execute logic - solve every rung top to bottom
    3. Write outputs - copy the output image table to the field outputs

PLCSimulator reproduces that cycle with a fixed, simulated scan time so
results are repeatable.
"""


class Program:
    """Base class for a ladder program.

    Subclasses declare their I/O and implement logic(dt). Inside logic(),
    read from self.I (input image) and write to self.O (output image).
    Internal bits (like B3 or BOOL tags) go in self.B.
    """

    INPUTS: tuple = ()
    OUTPUTS: tuple = ()
    INPUT_DEFAULTS: dict = {}   # e.g. NC stop buttons read True when not pressed

    def __init__(self):
        self.I = {name: self.INPUT_DEFAULTS.get(name, False) for name in self.INPUTS}
        self.O = {name: False for name in self.OUTPUTS}
        self.B = {}

    def logic(self, dt: int) -> None:
        raise NotImplementedError


class PLCSimulator:
    def __init__(self, program: Program, scan_time_ms: int = 10):
        self.program = program
        self.scan_time_ms = scan_time_ms
        self.time_ms = 0
        self.field_inputs = dict(program.I)
        self.field_outputs = dict(program.O)
        self.history = []   # (time_ms, outputs) every time an output changes

    # --- field side -------------------------------------------------------
    def set_input(self, name: str, value: bool) -> None:
        if name not in self.field_inputs:
            raise KeyError(f"Unknown input '{name}'. Valid: {list(self.field_inputs)}")
        self.field_inputs[name] = value

    def output(self, name: str) -> bool:
        return self.field_outputs[name]

    # --- scan cycle -------------------------------------------------------
    def scan(self) -> None:
        self.program.I.update(self.field_inputs)          # 1. read inputs
        self.program.logic(self.scan_time_ms)             # 2. execute logic
        changed = self.program.O != self.field_outputs
        self.field_outputs = dict(self.program.O)         # 3. write outputs
        self.time_ms += self.scan_time_ms
        if changed:
            self.history.append((self.time_ms, dict(self.field_outputs)))

    def run(self, duration_ms: int, on_scan=None) -> None:
        """Run scans for duration_ms. on_scan(sim) is called after each scan,
        which is where a plant model (tank, conveyor...) can react."""
        for _ in range(duration_ms // self.scan_time_ms):
            self.scan()
            if on_scan:
                on_scan(self)

    def pulse(self, name: str, ms: int = 100, on_scan=None) -> None:
        """Press and release a momentary input (like a push button)."""
        original = self.field_inputs[name]
        self.set_input(name, not original)
        self.run(ms, on_scan)
        self.set_input(name, original)
