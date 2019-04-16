import pytest
import json
from json import JSONEncoder
from ilastik_install import core
from test_constructor import random_data_w_prefix, random_text_w_prefix
import pathlib


class PosixPathEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, pathlib.Path):
            return str(o.as_posix())
        print(o)
        return JSONEncoder.default(self, o)


package_spec = {
    "paths_data": {
        "paths": [
            {
                "_path": "include/my_header.h",
                "file_mode": "text",
                "__occurences": 1,
                "prefix_placeholder": "/bld/anaconda1anaconda2anaconda3",
            },
            {
                "_path": "lib/pkgconfig/mylib-stubs.pc",
                "file_mode": "text",
                "prefix_placeholder": "/bld/anaconda1anaconda2anaconda3",
                "__occurences": 2,
            },
            {
                "_path": "lib/mylib.so.1.1.1",
                "file_mode": "binary",
                "prefix_placeholder": (
                    "/home/conda/feedstock_root/build_artifacts/mylib_1234456789"
                    "/_h_env_placehold_placehold_placehold_placehold_placehold_p"
                    "lacehold_placehold_placehold_placehold_placehold_placehold_"
                    "placehold_placehold_placehold_placehold_placehold_placehold_placehold"
                ),
                "__occurences": 23,
            },
        ]
    }
}


def generate_paths(tmp_path, current_prefix):
    files = package_spec["paths_data"]["paths"]
    for file in files:
        pp = tmp_path / file["_path"]
        pp.parent.mkdir(parents=True, exist_ok=True)
        if file["file_mode"] == "text":
            txt = random_text_w_prefix(200, current_prefix, file["__occurences"])
            with pp.open("w") as f:
                f.write(txt)
        elif file["file_mode"] == "binary":
            data = random_data_w_prefix(
                8400,
                file["prefix_placeholder"].encode("utf-8"),
                current_prefix.encode("utf-8"),
                file["__occurences"],
            )

            with (tmp_path / file["_path"]).open("wb") as f:
                f.write(data)
    conda_meta = tmp_path / "conda-meta"
    conda_meta.mkdir()
    with (conda_meta / "test_spec.json").open("w") as f:
        json.dump(package_spec, f, cls=PosixPathEncoder)


def check_prefixes(tmp_path, current_prefix, new_prefix):
    files = package_spec["paths_data"]["paths"]
    for file in files:
        pp = tmp_path / file["_path"]
        assert pp.exists()
        if file["file_mode"] == "text":
            with pp.open("r") as f:
                data = f.read()
                assert new_prefix.as_posix() in data
                assert current_prefix.as_posix() not in data
                assert data.count(new_prefix.as_posix()) == file["__occurences"]

        elif file["file_mode"] == "binary":
            with pp.open("rb") as f:
                data = f.read()
                assert new_prefix.as_posix().encode("utf-8") in data
                assert current_prefix.as_posix().encode("utf-8") not in data
                assert (
                    data.count(new_prefix.as_posix().encode("utf-8"))
                    == file["__occurences"]
                )


def test_main(tmp_path):
    """Dummy test in order to make conda build pass"""
    current_prefix = tmp_path / "somewhere" / "here"
    new_prefix = tmp_path / "somewhere" / "blah"
    generate_paths(tmp_path, current_prefix.as_posix())
    core.replace_prefixes(
        conda_meta_path=tmp_path / "conda-meta",
        root=tmp_path,
        current_placeholder=current_prefix,
        new_placeholder=new_prefix,
    )
    check_prefixes(tmp_path, current_prefix, new_prefix)
