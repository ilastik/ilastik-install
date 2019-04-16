"""
Test replacement operation.
"""
from ilastik_install.external import _constructor
import pathlib
import pytest
import random
import re
import string
import typing


def generate_random_data(random_str_len=2000) -> bytes:
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


def random_data_w_prefix(
    random_str_len: int, original_prefix: bytes, current_prefix: bytes, occurrences: int
) -> bytes:
    data = generate_random_data(random_str_len)
    len_diff = len(original_prefix) - len(current_prefix)
    bin_str = current_prefix + b"\0" * (len_diff + 1)
    assert occurrences * len(bin_str) < random_str_len
    assert data.count(original_prefix) == 0
    assert data.count(current_prefix) == 0
    interval_length = random_str_len // occurrences + 1
    for i in range(0, random_str_len, interval_length):
        start_pos = random.randint(i, i + interval_length - len(bin_str))
        data = inserted_to_binary(data, bin_str, start_pos)

    assert data.count(current_prefix) == occurrences
    return data


def zero_t(data: bytes) -> bytes:
    return data + b"\0"


@pytest.mark.parametrize(
    "original_prefix,current_prefix, new_prefix,occurrences",
    [
        (b"this_is_a_short_placeholder", b"short_current", b"short_new", 1),
        (b"AAAAA", b"BBBBB", b"CCCCC", 7),
        (b"AAAAA", b"BBB", b"CC", 1),
        (b"AAAAA", b"BBB", b"CCCCC", 12),
    ],
)
def test_replace(
    original_prefix: bytes, current_prefix: bytes, new_prefix: bytes, occurrences: int
):
    random_str_len = 2000
    random_data = random_data_w_prefix(
        random_str_len, original_prefix, current_prefix, occurrences
    )
    res = _constructor.binary_replace(
        random_data, original_prefix, current_prefix, new_prefix
    )
    assert res.count(new_prefix) == occurrences


@pytest.mark.parametrize(
    "nested_with,original_prefix,current_prefix,new_prefix,occurrences",
    [
        ((b"",), b"this_is_a_short_placeholder", b"short_current", b"short_new", 1),
        ((b"/something/here",), b"AAAAA", b"BBB", b"CCC", 10),
        ((b"/one/here", b"/other/one/here/yo"), b"AAAAA", b"BBB", b"CC", 11),
        ((b"/one/here", b"/other/one/here/yo"), b"AAAAA", b"BBB", b"CCCCC", 7),
    ],
)
def test_multi_nested_replace(
    nested_with: typing.Tuple[bytes],
    original_prefix: bytes,
    current_prefix: bytes,
    new_prefix: bytes,
    occurrences: int,
):
    random_str_len = 2000
    original_nested = b"".join([original_prefix + y for y in nested_with])
    current_nested = original_nested.replace(original_prefix, current_prefix)
    current_nested = current_nested + b"\0" * (
        len(original_nested) - len(current_nested)
    )

    random_data = random_data_w_prefix(
        random_str_len, original_nested, current_nested, occurrences
    )

    res = _constructor.binary_replace(
        random_data, original_prefix, current_prefix, new_prefix
    )
    assert res.count(zero_t(current_nested)) == 0
    assert res.count(zero_t(original_nested)) == 0

    new_nested = current_nested.rstrip(b"\0").replace(current_prefix, new_prefix)
    new_nested = new_nested + b"\0" * (len(original_nested) - len(new_nested))
    assert res.count(zero_t(new_nested)) == occurrences


def generate_random_text(random_str_len: int) -> typing.List[str]:
    prefix_count = 10
    mean_line_lenght = 80
    random_data = [
        "".join(
            random.choices(
                string.ascii_letters,
                k=max(0, round(random.normalvariate(mean_line_lenght, 20))),
            )
        )
        for x in range(random_str_len)
    ]
    return random_data


def random_text(random_str_len: int, current_prefix: str, occurrences: int) -> str:
    text = generate_random_text(random_str_len)
    lines = random.sample(range(random_str_len), k=occurrences)
    for line in lines:
        pos = random.randint(0, len(text[line]))
        text[line] = text[line][0:pos] + current_prefix + text[line][pos::]

    return "\n".join(text)


@pytest.mark.parametrize(
    "new_prefix,occurrences", [("1234", 1), ("1234567", 15), ("1234567890abcderfgh", 2)]
)
def test_update_prefix_text(new_prefix: str, occurrences: int, tmp_path: pathlib.Path):
    current_prefix = "something_random"
    original_prefix = "dontcare"
    random_str_len = 400
    txt = random_text(random_str_len, current_prefix, occurrences)
    txt_file = tmp_path / "txt-file.txt"
    with txt_file.open("w") as f:
        f.write(txt)

    mode: str = "text"
    _constructor.update_prefix(
        txt_file, original_prefix, current_prefix, new_prefix, mode
    )

    with txt_file.open("r") as f:
        txt_out = f.read()

    assert txt_out.count(new_prefix) == occurrences


@pytest.mark.parametrize(
    "new_prefix,occurrences", [("1234", 5), ("1234567", 3), ("1234567890abcderfgh1", 1)]
)
def test_update_prefix_text_binary(
    new_prefix: str, occurrences, tmp_path: pathlib.Path
):
    original_prefix = "123456789_max_length"
    current_prefix = "whatever"
    random_str_len = 2000
    random_data = random_data_w_prefix(
        random_str_len,
        original_prefix.encode("utf-8"),
        current_prefix.encode("utf-8"),
        occurrences,
    )

    bin_path = tmp_path / "binfile.bin"
    with bin_path.open("wb") as f:
        f.write(random_data)

    mode: str = "binary"
    _constructor.update_prefix(
        bin_path, original_prefix, current_prefix, new_prefix, mode
    )

    with bin_path.open("rb") as f:
        bin_out = f.read()

    assert bin_out.count(new_prefix.encode("utf-8")) == occurrences
