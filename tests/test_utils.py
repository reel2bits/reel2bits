from utils import duration_elapsed_human, duration_song_human, \
    get_hashed_filename
import time


def test_duration_elapsed_human():
    t = [
        {"duration": 20, "text": "right now"},
        {"duration": 0, "text": "right now"},
        {"duration": 200, "text": "3 mns"},
        {"duration": 36000, "text": "10 hs"},
        {"duration": 5184000, "text": "60 d"},
        {"duration": 1324512000, "text": "41 y"}
    ]
    for i in t:
        assert duration_elapsed_human(i["duration"]) == i["text"]


def test_duration_song_human():
    t = [
        {"duration": 20, "text": "20.00 secs"},
        {"duration": 0, "text": "0.00 secs"},
        {"duration": 265, "text": "4 mns"},
        {"duration": 36528, "text": "10 hours"},
        {"duration": 5999942, "text": "69 days"},
        {"duration": 1839937401, "text": "58 years"}
    ]
    for i in t:
        assert duration_song_human(i["duration"]) == i["text"]


def test_get_hashed_filename():
    a = get_hashed_filename("foo bar baz.mp3")
    time.sleep(3)
    b = get_hashed_filename("foo bar baz.mp3")
    time.sleep(1)
    c = get_hashed_filename("foo bar baz.mp3")
    time.sleep(0.4)
    d = get_hashed_filename("foo bar baz.mp3")
    assert a != b != c != d
