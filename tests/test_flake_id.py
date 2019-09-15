from utils.flake_id import gen_flakeid
import time


def test_gen_flakeid():
    for i in range(0, 100):
        a = gen_flakeid()
        b = gen_flakeid()
        assert a != b
        time.sleep(0.1)
