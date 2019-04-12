import pathlib
import typing
import dataclasses
import json

import logging

from ilastik_install.external import _constructor

logger = logging.getLogger(__name__)

ResultDict = typing.List[typing.Dict[str, str]]


@dataclasses.dataclass
class JsonConfig:
    spec_path: pathlib.Path
    json_specs: typing.Dict = dataclasses.field(init=False, repr=False)

    def __post_init__(self):
        with open(self.spec_path, "r") as f:
            self.json_specs = json.load(f)


class PackageSpec(JsonConfig):
    @property
    def file_iter(self):
        for file_spec in self.json_specs["paths_data"]["paths"]:
            if all(x in file_spec for x in ["file_mode", "prefix_placeholder"]):
                yield file_spec


def parse_conda_meta(
    conda_meta_path: pathlib.Path,
    root: pathlib.Path,
    current_placeholder: str,
    new_placeholder: str,
):
    logger.info(f"updating prefix_path from {current_placeholder} to {new_placeholder}")
    for json_file in conda_meta_path.glob("*.json"):
        pkg_spec = PackageSpec(json_file)
        for file_spec in pkg_spec.file_iter:
            fullpath = root / file_spec["_path"]
            mode = file_spec["file_mode"]

            assert fullpath.exists()
            logger.info(f"modifying {fullpath}:{mode}")
            _constructor.update_prefix(
                fullpath,
                new_placeholder.as_posix(),
                current_placeholder.as_posix(),
                mode,
            )
