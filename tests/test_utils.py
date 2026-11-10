from yt_fts.utils import time_to_secs


def test_time_to_secs_applies_buffer():
    assert time_to_secs("00:01:00") == 57
    assert time_to_secs("01:02:03") == 3720


def test_time_to_secs_never_goes_negative():
    assert time_to_secs("00:00:01") == 0
    assert time_to_secs("00:00:00") == 0
    assert time_to_secs("00:00:03") == 0
