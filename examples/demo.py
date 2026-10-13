"""Run a program and print a timeline of its outputs.

Usage:
    python examples/demo.py motor
    python examples/demo.py traffic
    python examples/demo.py tank
    python examples/demo.py conveyor
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ladder_sim import PLCSimulator  # noqa: E402
from programs import MotorStartStop, TrafficLight, TankFill, ConveyorSorter  # noqa: E402


def show(sim, title):
    print(f"\n=== {title} ===")
    print(f"{'time':>8}  outputs ON")
    for t, outs in sim.history:
        on = [name for name, v in outs.items() if v] or ["(all off)"]
        print(f"{t / 1000:>7.2f}s  {', '.join(on)}")


def demo_motor():
    sim = PLCSimulator(MotorStartStop())
    sim.run(500)
    sim.pulse("START_PB")          # operator presses START
    sim.run(2000)
    sim.set_input("OL_OK", False)  # overload trips
    sim.run(500)
    sim.set_input("OL_OK", True)   # overload reset
    sim.pulse("START_PB")
    sim.run(1000)
    sim.pulse("STOP_PB")
    show(sim, "Motor start/stop (start, overload trip, restart, stop)")


def demo_traffic():
    sim = PLCSimulator(TrafficLight())
    sim.set_input("RUN", True)
    sim.run(25_000)
    sim.set_input("RUN", False)
    sim.run(1000)
    show(sim, "Traffic light (two full cycles, then RUN off)")


class TankModel:
    """Very simple plant model: level in % with constant demand."""

    def __init__(self, level=10.0, fill_rate=4.0, demand=1.0):
        self.level, self.fill_rate, self.demand = level, fill_rate, demand

    def __call__(self, sim):
        dt_s = sim.scan_time_ms / 1000
        if sim.output("FILL_VALVE"):
            self.level += self.fill_rate * dt_s
        self.level = max(0.0, self.level - self.demand * dt_s)
        sim.set_input("LS_LOW", self.level >= 20)
        sim.set_input("LS_HIGH", self.level >= 80)
        sim.set_input("LS_HH", self.level >= 95)


def demo_tank():
    tank = TankModel()
    sim = PLCSimulator(TankFill())
    sim.pulse("START_PB", on_scan=tank)
    sim.run(150_000, on_scan=tank)
    show(sim, f"Tank fill (150 s, final level {tank.level:.0f}%)")
    # Now simulate a stuck valve: the valve opens but nothing flows
    tank.fill_rate = 0.0
    sim.run(60_000, on_scan=tank)
    show(sim, "Tank fill + stuck valve -> fill timeout fault")


def demo_conveyor():
    prog = ConveyorSorter(batch_size=5)
    sim = PLCSimulator(prog)
    sim.pulse("START_PB")
    for tall in (False, True, False, True, True):
        sim.set_input("HEIGHT_SENSOR", tall)
        sim.set_input("PE_ENTRY", True); sim.run(200)
        sim.set_input("PE_ENTRY", False); sim.set_input("HEIGHT_SENSOR", False)
        sim.run(1500)
        sim.set_input("PE_DIVERT", True); sim.run(200)
        sim.set_input("PE_DIVERT", False); sim.run(1500)
    sim.run(1000)
    show(sim, "Conveyor sorter (5 parts, 3 tall)")
    print(f"Total parts: {prog.C_TOTAL.ACC}   Tall parts: {prog.C_TALL.ACC}")


DEMOS = {"motor": demo_motor, "traffic": demo_traffic,
         "tank": demo_tank, "conveyor": demo_conveyor}

if __name__ == "__main__":
    names = sys.argv[1:] or list(DEMOS)
    for n in names:
        DEMOS[n]()
