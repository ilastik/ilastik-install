"""
Code here was originally taken from
    https://github.com/conda/constructor/blob/master/constructor/install.py

Thus the original copyright notice:

Copyright (c) 2016, Anaconda, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Anaconda, Inc. nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL ANACONDA, INC BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import os
import re
import sys
import stat


on_win = bool(sys.platform == "win32")


def exp_backoff_fn(fn, *args):
    """
    for retrying file operations that fail on Windows due to virus scanners
    """
    if not on_win:
        return fn(*args)

    import time
    import errno

    max_tries = 6  # max total time = 6.4 sec
    for n in range(max_tries):
        try:
            result = fn(*args)
        except (OSError, IOError) as e:
            if e.errno in (errno.EPERM, errno.EACCES):
                if n == max_tries - 1:
                    raise Exception("max_tries=%d reached" % max_tries)
                time.sleep(0.1 * (2 ** n))
            else:
                raise e
        else:
            return result


class PaddingError(Exception):
    pass


class PlaceholderLenghtError(Exception):
    pass


def binary_replace(
    data: bytes,
    original_placeholder: bytes,
    current_placeholder: bytes,
    new_placeholder: bytes,
):
    """
    Perform a binary replacement of `data`, where the placeholder
    `current_placeholder` is replaced with `new_placeholder` (terminated with a
    single b"\0) and the remaining string is kept untouched.
    `new_placeholder` may not be longer than `original_placeholder`.
    All input arguments are expected to be bytes objects.
    |-----------------------original placeholder-----------------|somestring?|0|
    |--------current placeholder--------|somestring?|00000000000000000000000000|
    |------------new placeholder--------------|somestr?|00000000000000000000000|
    """
    if len(new_placeholder) > len(original_placeholder):
        raise PlaceholderLenghtError(
            f"New placeholder longer (lenght: {len(new_placeholder)}) than "
            f"old placholder (length: {len(original_placeholder)}).",
            original_placeholder,
            new_placeholder,
        )
    # sanity checks!
    padding_current = len(original_placeholder) - len(current_placeholder)
    padding_new = len(original_placeholder) - len(current_placeholder)
    assert padding_current >= 0
    assert padding_new >= 0

    def replace(match):
        """
        replace `current_placeholder` with `new_placeholder` and make sure the
        resulting bytes have the same length (padded with \0)
        """
        matchstr = match.group().rstrip(b"\0")
        result = matchstr.replace(current_placeholder, new_placeholder)
        result = result + b"\0" * (len(match.group()) - len(result))
        assert len(result) == len(match.group())
        return result

    # find the string including all trailing \0s
    pat = re.compile(re.escape(current_placeholder) + b"([^\0]*?)\0+")
    res = pat.sub(replace, data)

    assert new_placeholder in res
    assert len(res) == len(data)
    return res


def update_prefix(
    path: str, original_prefix: str, current_prefix: str, new_prefix: str, mode: str
):
    if on_win:
        # force all prefix replacements to forward slashes to simplify need
        # to escape backslashes - replace with unix-style path separators
        new_prefix = new_prefix.replace("\\", "/")

    path = os.path.realpath(path)
    with open(path, "rb") as fi:
        data = fi.read()
    if mode == "text":
        new_data = data.replace(
            current_prefix.encode("utf-8"), new_prefix.encode("utf-8")
        )
    elif mode == "binary":
        if on_win:
            # anaconda-verify will not allow binary current_prefix on Windows.
            # However, since some packages might be created wrong (and a
            # binary current_prefix would break the package, we just skip here.
            return
        new_data = binary_replace(
            data,
            original_prefix.encode("utf-8"),
            current_prefix.encode("utf-8"),
            new_prefix.encode("utf-8"),
        )
    else:
        sys.exit("Invalid mode:" % mode)

    if new_data == data:
        return
    st = os.lstat(path)
    # unlink in case the file is memory mapped
    exp_backoff_fn(os.unlink, path)
    with open(path, "wb") as fo:
        fo.write(new_data)
    os.chmod(path, stat.S_IMODE(st.st_mode))
