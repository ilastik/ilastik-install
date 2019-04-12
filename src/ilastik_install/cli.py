import pathlib
from argparse import ArgumentParser, Namespace
import logging


logger = logging.getLogger(__name__)


def parse_args() -> Namespace:
    p = ArgumentParser(
        description="Install/relocate tool for ilastik",
        usage="Should in general not use arguments.",
    )

    p.add_argument(
        "root-path",
        type=pathlib.Path,
        help="Root of the ilastik install (same as run_ilastik.sh).",
    )
    p.add_argument(
        "--override-prefix-file",
        type=str,
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
    args = parse_args()
    print(args)
