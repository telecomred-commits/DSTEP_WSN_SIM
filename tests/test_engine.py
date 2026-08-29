from wsn_sim.core.event_engine import EventEngine

def test_event_order():
    engine = EventEngine()
    result = []

    engine.schedule(2.0, lambda: result.append(2))
    engine.schedule(1.0, lambda: result.append(1))
    engine.run(3.0)

    assert result == [1, 2]
