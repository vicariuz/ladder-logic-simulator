from ladder_sim import TON, TOF, Counter, OneShot, OneShotFalling


def run_timer(timer, rung, ms, dt=10):
    for _ in range(ms // dt):
        timer.update(rung, dt)


def test_ton_times_and_resets():
    t = TON(1000)
    run_timer(t, True, 990)
    assert t.TT and not t.DN
    run_timer(t, True, 10)
    assert t.DN and not t.TT and t.ACC == 1000
    run_timer(t, False, 10)
    assert not t.DN and t.ACC == 0


def test_ton_interrupted_starts_over():
    t = TON(1000)
    run_timer(t, True, 600)
    run_timer(t, False, 10)
    run_timer(t, True, 600)
    assert not t.DN  # ACC was reset, only 600 ms accumulated


def test_tof_holds_after_rung_goes_false():
    t = TOF(500)
    assert not t.DN                 # off at power-up
    run_timer(t, True, 10)
    assert t.DN
    run_timer(t, False, 490)
    assert t.DN and t.TT
    run_timer(t, False, 10)
    assert not t.DN and not t.TT


def test_counter_counts_edges_not_levels():
    c = Counter(3)
    for _ in range(5):
        c.ctu(True)                 # held true: counts once
    assert c.ACC == 1
    for _ in range(2):
        c.ctu(False)
        c.ctu(True)
    assert c.ACC == 3 and c.DN
    c.ctd(True)
    assert c.ACC == 2 and not c.DN
    c.res()
    assert c.ACC == 0


def test_one_shots():
    ons, osf = OneShot(), OneShotFalling()
    assert [ons.update(v) for v in (False, True, True, False, True)] == \
           [False, True, False, False, True]
    assert [osf.update(v) for v in (True, True, False, False)] == \
           [False, False, True, False]
