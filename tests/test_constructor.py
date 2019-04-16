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
        (b"AAAAA", b"BBBBB", b"CCCCC"),
        (b"AAAAA", b"BBB", b"CC"),
        (b"AAAAA", b"BBB", b"CCCCC"),
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
        (b"AAAAA", b"BBBBB", b"CCCCC"),
        (b"AAAAA", b"BBBB", b"CCC"),
        (b"AAAAA", b"BBB", b"CCCCC"),
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
        ((b"/something/here",), b"AAAAA", b"BBB", b"CCC"),
        ((b"/one/here", b"/other/one/here/yo"), b"AAAAA", b"BBB", b"CC"),
        ((b"/one/here", b"/other/one/here/yo"), b"AAAAA", b"BBB", b"CCCCC"),
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
        random_str_len // 2, random_str_len - repl_string_len - 1
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

    new_nested = current_nested.rstrip(b"\0").replace(current_prefix, new_prefix)
    new_nested = new_nested + b"\0" * (len(original_nested) - len(new_nested))
    assert res.count(zero_t(new_nested)) == 2


@pytest.fixture
def random_text() -> typing.Tuple[str, str]:
    n_lines = 2000
    prefix_count = 10
    mean_line_lenght = 80
    random_data = [
        "".join(
            random.choices(
                string.ascii_letters,
                k=max(0, round(random.normalvariate(mean_line_lenght, 20))),
            )
        )
        for x in range(n_lines)
    ]

    current_prefix = "12345678"
    lines = random.sample(range(n_lines), k=prefix_count)
    for line in lines:
        pos = random.randint(0, len(random_data[line]))
        random_data[line] = (
            random_data[line][0:pos] + current_prefix + random_data[line][pos::]
        )

    return current_prefix, "\n".join(random_data)


@pytest.fixture
def text_file(
    tmp_path: pathlib.Path, random_text: str
) -> typing.Tuple[str, pathlib.Path]:
    txt_file = tmp_path / "textfile.txt"
    with txt_file.open("w") as f:
        prefix, text = random_text
        f.write(text)
    return prefix, txt_file


@pytest.mark.parametrize("new_prefix", ["1234", "1234567", "1234567890abcderfgh"])
def test_update_prefix_text(new_prefix: str, text_file):
    original_prefix: str = "norealneed"
    current_prefix, path = text_file
    mode: str = "text"
    _constructor.update_prefix(path, original_prefix, current_prefix, new_prefix, mode)

    with path.open("r") as f:
        txt_out = f.read()

    assert txt_out.count(new_prefix) == 10


@pytest.fixture
def binary_file(
    tmp_path: pathlib.Path, random_data: bytes
) -> typing.Tuple[str, pathlib.Path]:
    bin_file = tmp_path / "binfile.bin"
    original_prefix = "123456789_max_length"
    prefix = "whatever"
    len_diff = len(original_prefix) - len(prefix)
    bin_data = inserted_to_binary(
        random_data, zero_t(prefix.encode("utf-8")) + b"\0" * len_diff, 100
    )

    with bin_file.open("wb") as f:
        f.write(bin_data)
    return prefix, bin_file


@pytest.mark.parametrize("new_prefix", ["1234", "1234567", "1234567890abcderfgh1"])
def test_update_prefix_text_binary(new_prefix, binary_file):
    original_prefix: str = "123456789_max_length"
    current_prefix, path = binary_file
    mode: str = "binary"
    _constructor.update_prefix(path, original_prefix, current_prefix, new_prefix, mode)

    with path.open("rb") as f:
        bin_out = f.read()

    assert bin_out.count(new_prefix.encode("utf-8")) == 1
