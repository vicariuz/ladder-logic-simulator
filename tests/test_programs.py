from ladder_sim import PLCSimulator
from programs import MotorStartStop, TrafficLight, TankFill, ConveyorSorter


def test_motor_start_seal_in_and_stop():
    sim = PLCSimulator(MotorStartStop())
    sim.pulse("START_PB")
    sim.run(500)
    assert sim.output("MOTOR")          # sealed in after releasing START
    sim.pulse("STOP_PB")                # NC button: pulse opens it
    assert not sim.output("MOTOR")


def test_motor_trips_on_overload():
    sim = PLCSimulator(MotorStartStop())
    sim.pulse("START_PB")
    sim.set_input("OL_OK", False)
    sim.run(20)
    assert not sim.output("MOTOR")


def test_traffic_light_sequence():
    sim = PLCSimulator(TrafficLight(green_ms=1000, yellow_ms=500, red_ms=1000))
    sim.set_input("RUN", True)
    sim.run(500)
    assert sim.output("GREEN")
    sim.run(700)                        # t = 1.2 s
    assert sim.output("YELLOW") and not sim.output("GREEN")
    sim.run(500)                        # t = 1.7 s
    assert sim.output("RED")
    sim.run(1100)                       # t = 2.8 s -> new cycle
    assert sim.output("GREEN")
    # exactly one light on at every moment
    for _, outs in sim.history:
        assert sum(outs.values()) == 1


def test_tank_fills_between_low_and_high():
    sim = PLCSimulator(TankFill())
    sim.pulse("START_PB")
    sim.run(20)
    assert sim.output("FILL_VALVE")     # level below LS_LOW
    sim.set_input("LS_LOW", True)
    sim.run(20)
    assert sim.output("FILL_VALVE")     # keeps filling (seal-in)
    sim.set_input("LS_HIGH", True)
    sim.run(20)
    assert not sim.output("FILL_VALVE")
    sim.set_input("LS_HIGH", False)     # level drops a bit, still above low
    sim.run(20)
    assert not sim.output("FILL_VALVE") # hysteresis: no restart yet


def test_tank_fill_timeout_latches_fault():
    sim = PLCSimulator(TankFill(fill_timeout_ms=2000))
    sim.pulse("START_PB")
    sim.run(2100)                       # level never rises: stuck valve
    assert sim.output("ALARM") and not sim.output("FILL_VALVE")
    sim.pulse("RESET_PB")
    sim.run(20)
    assert not sim.output("ALARM") and sim.output("FILL_VALVE")


def pass_part(sim, tall):
    sim.set_input("HEIGHT_SENSOR", tall)
    sim.set_input("PE_ENTRY", True); sim.run(200)
    sim.set_input("PE_ENTRY", False); sim.set_input("HEIGHT_SENSOR", False)
    sim.run(1000)                       # travel to diverter
    sim.set_input("PE_DIVERT", True); sim.run(200)
    diverted = sim.output("DIVERTER")
    sim.set_input("PE_DIVERT", False); sim.run(1000)
    return diverted


def test_conveyor_diverts_only_tall_parts_and_counts():
    prog = ConveyorSorter(batch_size=4)
    sim = PLCSimulator(prog)
    sim.pulse("START_PB")
    results = [pass_part(sim, tall) for tall in (True, False, True)]
    assert results == [True, False, True]
    assert prog.C_TOTAL.ACC == 3 and prog.C_TALL.ACC == 2
    assert sim.output("MOTOR")


def test_conveyor_stops_when_batch_done_and_resets():
    prog = ConveyorSorter(batch_size=2)
    sim = PLCSimulator(prog)
    sim.pulse("START_PB")
    pass_part(sim, False)
    pass_part(sim, False)
    assert sim.output("BATCH_DONE") and not sim.output("MOTOR")
    sim.pulse("RESET_PB")
    sim.pulse("START_PB")
    assert sim.output("MOTOR") and not sim.output("BATCH_DONE")
