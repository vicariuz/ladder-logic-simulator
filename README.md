# Ladder Logic Simulator

An educational PLC simulator written in Python. It reproduces the PLC **scan cycle** and the most common ladder instructions, modeled after **Rockwell Logix / Studio 5000**, so you can practice real control logic before touching hardware.

Every program includes its ladder rungs as comments next to the Python code, so you can read both side by side.

## What's inside

| Instruction | Logix equivalent | Behavior |
|---|---|---|
| `TON` | Timer On-Delay | Output turns on after the rung has been true for `PRE` ms. Resets when the rung goes false. |
| `TOF` | Timer Off-Delay | Output turns on immediately and stays on for `PRE` ms after the rung goes false. |
| `Counter.ctu / ctd / res` | CTU / CTD / RES | Counts rising edges, `DN` when `ACC >= PRE`. |
| `OneShot` / `OneShotFalling` | ONS / OSF | True for exactly one scan on a rising / falling edge. |

Status bits follow Logix naming: `.PRE`, `.ACC`, `.EN`, `.TT`, `.DN`.

### The scan cycle

`PLCSimulator` repeats the same three steps a real PLC does, with a fixed simulated scan time (10 ms by default):

1. **Read inputs** into the input image table
2. **Execute logic**, top rung to bottom rung
3. **Write outputs** from the output image table

Because time is simulated, every run is deterministic and testable.

## Example programs

| Program | Concepts practiced |
|---|---|
| `MotorStartStop` | Seal-in contact, NC stop button and overload wired fail-safe |
| `TrafficLight` | Cascaded `TON` timers that reset each other to form a cycle |
| `TankFill` | Level hysteresis (low/high switches), high-high alarm, fill-timeout fault with latch/unlatch and reset |
| `ConveyorSorter` | Photo-eyes, `ONS` edge detection, `CTU` batch counting, `TOF` diverter hold, auto-stop when the batch is done and the belt is clear |

Example rung, from `MotorStartStop`:

```
|  START_PB     STOP_PB   OL_OK       MOTOR  |
|----] [----+----] [-------] [---------( )----|
|  MOTOR    |                                 |
|----] [----+                                 |
```

```python
O["MOTOR"] = (I["START_PB"] or O["MOTOR"]) and I["STOP_PB"] and I["OL_OK"]
```

## Quick start

```bash
git clone https://github.com/vicariuz/ladder-logic-simulator.git
cd ladder-logic-simulator
python examples/demo.py            # run every demo
python examples/demo.py tank       # or just one: motor | traffic | tank | conveyor
```

Sample output (tank with a stuck valve triggering the fill-timeout fault):

```
=== Tank fill + stuck valve -> fill timeout fault ===
    time  outputs ON
 163.41s  SYSTEM_ON, FILL_VALVE
 193.40s  SYSTEM_ON, FILL_VALVE, ALARM
 193.41s  SYSTEM_ON, ALARM
```

Notice the single scan where `FILL_VALVE` and `ALARM` are both on: the fault is latched on a rung *below* the valve rung, so the valve only drops on the next scan. Rung order matters, just like in a real PLC.

## Write your own program

```python
from ladder_sim import Program, PLCSimulator, TON

class DelayedStart(Program):
    INPUTS = ("START",)
    OUTPUTS = ("MOTOR",)

    def __init__(self):
        super().__init__()
        self.T1 = TON(3000)

    def logic(self, dt):
        self.T1.update(self.I["START"], dt)
        self.O["MOTOR"] = self.T1.DN

sim = PLCSimulator(DelayedStart())
sim.set_input("START", True)
sim.run(3500)
print(sim.output("MOTOR"))   # True
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Project structure

```
ladder_sim/      core engine (scan cycle) and instructions
programs/        example ladder programs
examples/demo.py runnable demos with output timelines
tests/           pytest suite for instructions and programs
```

## Roadmap

- [x] Scan-cycle engine, TON / TOF, CTU / CTD / RES, ONS / OSF
- [x] Motor start/stop, traffic light, tank fill, conveyor sorter
- [ ] Shift register / FIFO (BSL, FFL / FFU) to track multiple parts on the conveyor
- [ ] Retentive timer (RTO) and math / compare instructions (GRT, LES, EQU, ADD)
- [ ] Web HMI to visualize I/O in real time
- [ ] Data collection to SQL / OPC UA

## Why this project

I troubleshoot electrical, sensor, and mechanical faults on automated lines (FANUC robots, conveyors, AGVs). This simulator is how I practice the control logic side: understanding why a machine does what it does, not just what failed.
