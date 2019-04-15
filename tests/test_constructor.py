"""
Test replacement operation.
"""
from ilastik_install.external import _constructor
import pytest
import random
import re
import typing


@pytest.fixture
def random_data() -> bytes:
    random_str_len = 2000
    random_data = bytes(
        "".join([chr(random.randint(0, 1114111)) for x in range(random_str_len)]),
        "utf-32",
        errors="replace",
    )
    return random_data


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
        (b"this_is_a_short_placeholder", b"short_current", b"short_new"),
        (b"AAA", b"BBB", b"CCC"),
        (b"AAA", b"BB", b"C"),
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
        (b"this_is_a_short_placeholder", b"short_current", b"short_new"),
        (b"AAA", b"BBB", b"CCC"),
        (b"AAA", b"BB", b"C"),
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


@pytest.mark.parametrize(
    "nested_with,original_prefix,current_prefix, new_prefix",
    [
        ((b"",), b"this_is_a_short_placeholder", b"short_current", b"short_new"),
        ((b"/something/here",), b"AAA", b"BBB", b"CCC"),
        ((b"/one/here", b"/other/one/here/yo"), b"AAA", b"BB", b"C"),
    ],
)
def test_multi_nested_replace(
    nested_with: typing.Tuple[bytes],
    original_prefix: bytes,
    current_prefix: bytes,
    new_prefix: bytes,
    random_data: bytes,
):
    assert random_data.count(original_prefix) == 0
    random_str_len = len(random_data)
    original_nested = b"".join([original_prefix + y for y in nested_with])
    repl_string_len = len(original_nested)

    # insert the original prefix
    start_pos = random.randint(0, random_str_len // 2 - repl_string_len - 1)
    random_data = inserted_to_binary(random_data, original_nested, start_pos)
    assert random_data.count(original_prefix) == len(nested_with)

    # n+1: insert the original prefix
    start_pos = random.randint(
        random_str_len // 2, random_str_len - len(original_prefix) - 1
    )
    random_data = inserted_to_binary(random_data, original_nested, start_pos)
    assert random_data.count(original_prefix) == 2 * len(nested_with)

    current_nested = original_nested.replace(original_prefix, current_prefix)
    current_nested = current_nested + b"\0" * (
        len(original_nested) - len(current_nested)
    )
    assert len(current_nested) == len(original_nested)
    # insert the current prefix
    random_data = re.sub(re.escape(original_nested), current_nested, random_data)
    assert random_data.count(original_prefix) == 0
    assert random_data.count(current_prefix) == 2 * len(nested_with)

    res = _constructor.binary_replace(
        random_data, original_prefix, current_prefix, new_prefix
    )
    assert res.count(zero_t(current_nested)) == 0
    assert res.count(zero_t(original_nested)) == 0

    new_nested = current_nested.replace(current_prefix, new_prefix)
    new_nested = new_nested + b"\0" * (len(current_nested) - len(new_nested))

    assert res.count(zero_t(new_nested)) == 2
