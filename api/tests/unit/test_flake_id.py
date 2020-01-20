from utils.flake_id import FlakeId
import time
import uuid

TEST_ROUNDS = 1000


def test_always_same_length():
    """Test that FlakeIDs are all the same length"""
    flocons = FlakeId()

    lengths = []
    for i in range(0, TEST_ROUNDS):
        flake = flocons.get()
        length = flake.bit_length()
        lengths.append(length)
        time.sleep(0.001)
    assert len(lengths) == 1000
    # get uniques
    lengths = list(set(lengths))
    # we should have only one
    assert len(lengths) == 1


def test_always_unique():
    """Test that FlakeIDs are sorta unique"""
    flocons = FlakeId()

    flakes = []
    flakes.append(flocons.get())
    time.sleep(0.1)

    for i in range(0, TEST_ROUNDS):
        flake = flocons.get()
        assert flake not in flakes
        flakes.append(flake)
        time.sleep(0.01)


def test_always_bigger_than_previous():
    """Test that FlakeIDs are always bigger then previous one"""
    flocons = FlakeId()

    last_flake = flocons.get()
    last_uuid = uuid.UUID(int=last_flake)

    for i in range(0, TEST_ROUNDS):
        new_flake = flocons.get()
        assert new_flake > last_flake

        new_uuid = uuid.UUID(int=new_flake)
        assert new_uuid > last_uuid

        last_flake = new_flake
        last_uuid = new_uuid
