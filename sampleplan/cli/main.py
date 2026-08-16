import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import List, Optional

from sampleplan.cli.commands import ci, double, sequential, single
from sampleplan.cli.common import CliError

COMMANDS = [ci, single, double, sequential]

DESCRIPTION = """\
Determine sample sizes required for data quality control.

The following parameters describe the statistical guarantees one wants from the tests:

  alpha          Rejecting a lot that should have been accepted (producer's risk)
  beta           Accepting a lot that should have been rejected (consumer's risk)
  p0 / p         The assumed error rate
  ci-half-width  The size of the confidence interval in one direction
  p-a            Acceptable ratio of defective items in a lot
  p-r            Unacceptable ratio of defective items in a lot
"""


def _version() -> str:
    try:
        return version("sampleplan")
    except PackageNotFoundError:
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sampleplan",
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_version()}")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    for command in COMMANDS:
        command.register(subparsers)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        args.func(args)
    except (CliError, ValueError, AssertionError) as e:
        parser.exit(2, f"{parser.prog} {args.command}: error: {e}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
