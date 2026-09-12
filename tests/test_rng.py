from sciti.rng import make_streams, STREAMS


def test_streams_repeat_for_same_seed():
    a, b = make_streams(5), make_streams(5)
    for name in STREAMS:
        assert a[name].random() == b[name].random()


def test_streams_are_independent_of_each_other():
    s = make_streams(5)
    before = make_streams(5)["demand"].random(3)
    s["ops"].random(1000)  # consuming one stream must not change another
    assert (s["demand"].random(3) == before).all()
