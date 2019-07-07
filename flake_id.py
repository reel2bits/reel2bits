import time
import threading
import os
import random


def gen_flakeid():
    # (64b ?) timestamp in ns
    t = str(time.time_ns())

    # (48b) "worker id", rand
    w = random.getrandbits(48)

    pid = os.getpid()
    tid = threading.get_ident()
    ptid = f"{pid}{tid}"

    # (16b) sequence from PID+threadID
    # might be possible to throw in the
    # object id of the flask request
    s = hash(ptid) & 65536

    return int(f"{t}{w}{s}")
