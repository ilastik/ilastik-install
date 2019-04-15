"""
Test replacement operation.
"""
from ilastik_install.external import _constructor
import pytest
import random
import re


@pytest.fixture
def random_data() -> bytes:
    random_str_len = 2000
    random_data = bytes(
        "".join([chr(random.randint(0, 1114111)) for x in range(random_str_len)]),
        "utf-32",
        errors="replace",
    )
    return random_data


def as_encoded_bytes(some_str: str) -> bytes:
    return some_str.encode("utf-8")


def inserted_to_binary(data: bytes, repl: bytes, start_pos: int) -> bytes:
    """Returns data with same length and repl inserted at start_pos"""
    assert start_pos < (len(data) - len(repl))
    assert start_pos >= 0
    return data[0:start_pos] + repl + b"\0" + data[start_pos + len(repl) + 1 : :]


def zero_t(data: bytes) -> bytes:
    return data + b"\0"


@pytest.mark.parametrize(
    "original_prefix,current_prefix, new_prefix",
    [
        (
            as_encoded_bytes("this_is_a_short_placeholder"),
            as_encoded_bytes("short_current"),
            as_encoded_bytes("short_new"),
        ),
        (as_encoded_bytes("AAA"), as_encoded_bytes("BBB"), as_encoded_bytes("CCC")),
        (as_encoded_bytes("AAA"), as_encoded_bytes("BB"), as_encoded_bytes("C")),
    ],
)
def test_single_replace(
    original_prefix: bytes, current_prefix: bytes, new_prefix: bytes, random_data: bytes
):
    random_str_len = len(random_data)
    assert random_data.count(original_prefix) == 0
    # insert the original prefix
    start_pos = random.randint(0, random_str_len - len(original_prefix) - 1)
    random_data = inserted_to_binary(random_data, original_prefix, start_pos)
    assert random_data.count(original_prefix) == 1
    # insert the current prefix
    random_data = re.sub(
        re.escape(original_prefix) + b"\0",
        current_prefix + b"\0" * (len(original_prefix) - len(current_prefix) + 1),
        random_data,
    )

    assert current_prefix in random_data
    res = _constructor.binary_replace(
        random_data, original_prefix, current_prefix, new_prefix
    )
    assert new_prefix in res


@pytest.mark.parametrize(
    "original_prefix,current_prefix, new_prefix",
    [
        (
            as_encoded_bytes("this_is_a_short_placeholder"),
            as_encoded_bytes("short_current"),
            as_encoded_bytes("short_new"),
        ),
        (as_encoded_bytes("AAA"), as_encoded_bytes("BBB"), as_encoded_bytes("CCC")),
        (as_encoded_bytes("AAA"), as_encoded_bytes("BB"), as_encoded_bytes("C")),
    ],
)
def test_multi_replace(
    original_prefix: bytes, current_prefix: bytes, new_prefix: bytes, random_data: bytes
):
    random_str_len = len(random_data)
    assert random_data.count(original_prefix) == 0
    # insert the original prefix
    start_pos = random.randint(0, random_str_len // 2 - len(original_prefix) - 1)
    random_data = inserted_to_binary(random_data, original_prefix, start_pos)
    assert random_data.count(original_prefix) == 1

    # n+1: insert the original prefix
    start_pos = random.randint(
        random_str_len // 2, random_str_len - len(original_prefix) - 1
    )
    random_data = inserted_to_binary(random_data, original_prefix, start_pos)
    assert random_data.count(original_prefix) == 2

    # insert the current prefix
    random_data = re.sub(
        re.escape(original_prefix) + b"\0",
        current_prefix + b"\0" * (len(original_prefix) - len(current_prefix) + 1),
        random_data,
    )
    assert random_data.count(zero_t(original_prefix)) == 0
    assert random_data.count(zero_t(current_prefix)) == 2

    res = _constructor.binary_replace(
        random_data, original_prefix, current_prefix, new_prefix
    )
    assert res.count(zero_t(new_prefix)) == 2
    assert random_data.count(zero_t(original_prefix)) == 0
