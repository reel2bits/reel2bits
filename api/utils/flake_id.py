import time
import threading
import os
import random
import binascii
import warnings

"""
k-ordered ID generation thingy
adapted from https://git.pleroma.social/pleroma/flake_id
"""

# Hack for python <=3.6; time_ns is >=3.7
if not hasattr(time, "time_ns"):
    time.time_ns = lambda: int(time.time() * 1e9)


# The FlakeId.get() should return a 128bit integer
# Which should be able to be fed to uuid.UUID(int=FlakeId.get())


class FlakeId(object):
    def __init__(self):
        self.state_node = self.worker_id()
        self.state_time = 0
        self.state_sq = 0

    def worker_id(self):
        """Worker ID generated from PID, ThreadID and 16bit random thing"""
        random_bits = random.getrandbits(16)
        # more cursed random things
        pid = os.getpid()
        tid = threading.get_ident()
        ptid = f"{pid}{random_bits}{tid}"
        return binascii.crc32(ptid.encode("utf-8"))

    def time(self):
        """some length cursed timestamp"""
        # docs don't seem to guarantee this to be 64bits so here's a bitmask
        return time.time_ns() & 0xFFFF_FFFF_FFFF_FFFF

    def gen_flakeid(self):
        fid_time = format(self.state_time, "064b")  # 64bit
        fid_node = format(self.state_node, "048b")  # 48bit
        fid_seq = format(self.state_sq, "016b")  # 16bit
        # return a big 128bit binary string
        return f"{fid_time}{fid_node}{fid_seq}"

    def get(self):
        """Return a Flake ID"""
        # Increment sequence on call
        self.state_sq = (self.state_sq + 1) & 0xFFFF
        # Get time
        self.state_time = self.time()
        # Get a Flake ID
        flake_id = self.gen_flakeid()
        return int(flake_id, 2)


def gen_flakeid():
    warnings.warn("Use the class FlakeId.get() instead", DeprecationWarning, stacklevel=2)
    # (64 bits) timestamp in ns
    t = time.time_ns()

    # (47 bits + 1 extra) "worker id", rand
    # https://stackoverflow.com/questions/17125237/getrandbits-does-not-produce-constant-length-numbers
    # computers are bad
    w = random.getrandbits(47) + (1 << 47)

    pid = os.getpid()
    tid = threading.get_ident()
    ptid = f"{pid}{tid}"

    # (16b) sequence from PID+threadID
    # might be possible to throw in the
    # object id of the flask request
    # 32bit crc
    s = binascii.crc32(ptid.encode("utf-8"))
    # butcher it
    s = s & 0xFFFF

    return int(f"{t}{w}{s}")
