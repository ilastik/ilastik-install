import pathlib
from argparse import ArgumentParser, Namespace
import logging
from ilastik_install import core
import dataclasses

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class PrefixConfig(core.JsonConfig):
    root_path: pathlib.Path
    clean: bool = dataclasses.field(init=False)
    prefix: bool = dataclasses.field(init=False)
    valid: bool = dataclasses.field(init=False)

    def __post_init__(self):
        super().__post_init__()
        self.valid = self.spec_path.parent == self.root_path
        self.prefix = pathlib.Path(self.json_specs["previous_prefix"])
        self.clean = self.valid and self.prefix == self.root_path


def parse_args() -> Namespace:
    p = ArgumentParser(
        description="Install/relocate tool for ilastik",
        usage="Should in general not use arguments.",
    )

    p.add_argument(
        "root",
        type=pathlib.Path,
        help="Root of the ilastik install (same as run_ilastik.sh).",
    )
    p.add_argument(
        "--override-prefix-file",
        type=str,
        default="",
        help=(
            "Should normally not be used, override the prefix file that stores "
            "the previous prefix."
        ),
    )
    p.add_argument(
        "--new-prefix",
        type=str,
        help="New prefix to replace the old one with." "Will be derived with.",
    )

    args = p.parse_args()
    return args


def main():
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(name)s-%(levelname)s: %(message)s"
    )
    args = parse_args()

    spec_file = ".prefix_previous"
    if args.override_prefix_file != "":
        logger.warning(
            f"Not running with default value for prefix file. Using {args.override_prefix_file} instead"
        )
        spec_file = args.override_prefix_file

    spec_file = args.root / spec_file
    if not spec_file.exists():
        logger.error(f"Could not find spec file at {spec_file}")

    prefix_config = PrefixConfig(spec_file, args.root)
    logger.debug(prefix_config)

    core.replace_prefixes(
        args.root / "conda-meta", args.root, prefix_config.prefix, args.root
    )


if __name__ == "__main__":
    main()
