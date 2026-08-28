import argparse
import json
from typing import Any, Callable, Dict, List, TypeVar

from sampleplan.service import BINOMIAL, DEFAULT_ALPHA, DEFAULT_BETA, HYPERGEOMETRIC

T = TypeVar("T", int, float)


def bounded(
    converter: Callable[[str], T],
    predicate: Callable[[T], bool],
    expectation: str,
) -> Callable[[str], T]:
    """Builds an argparse type that parses a value and checks it against `predicate`."""

    def _parse(value: str) -> T:
        try:
            result = converter(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{value}' is not a valid {converter.__name__}")

        if not predicate(result):
            raise argparse.ArgumentTypeError(f"'{value}' has to be {expectation}")

        return result

    return _parse


probability = bounded(float, lambda x: 0.0 < x < 1.0, "strictly between 0 and 1")
positive_int = bounded(int, lambda x: x > 0, "larger than 0")
non_negative_int = bounded(int, lambda x: x >= 0, "0 or larger")


def add_distribution_arg(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-d",
        "--distribution",
        required=True,
        choices=[BINOMIAL, HYPERGEOMETRIC],
        help="Binomial for sampling with replacement, hypergeometric for sampling without replacement",
    )


def add_lot_size_arg(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--lot-size",
        type=positive_int,
        help="Size of the lot, required for the hypergeometric distribution",
    )


def add_risk_args(parser: argparse.ArgumentParser, with_beta: bool = True):
    parser.add_argument(
        "--alpha",
        type=probability,
        default=DEFAULT_ALPHA,
        help="Producer's risk: rejecting a lot that should have been accepted (default: %(default)s)",
    )

    if with_beta:
        parser.add_argument(
            "--beta",
            type=probability,
            default=DEFAULT_BETA,
            help="Consumer's risk: accepting a lot that should have been rejected (default: %(default)s)",
        )


def add_quality_level_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--p-a",
        type=probability,
        required=True,
        help="Acceptable ratio of defective items in a lot",
    )
    parser.add_argument(
        "--p-r",
        type=probability,
        required=True,
        help="Unacceptable ratio of defective items in a lot",
    )


def add_output_args(parser: argparse.ArgumentParser):
    parser.add_argument("--json", action="store_true", help="Print the result as JSON instead of plain text")


def emit(payload: Dict[str, Any], lines: List[str], as_json: bool):
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        for line in lines:
            print(line)
