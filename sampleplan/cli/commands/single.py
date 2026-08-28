import argparse

from sampleplan.cli.common import (
    add_distribution_arg,
    add_lot_size_arg,
    add_output_args,
    add_quality_level_args,
    add_risk_args,
    emit,
    positive_int,
)
from sampleplan.service import DEFAULT_LIMIT, compute_single


def register(subparsers):
    parser = subparsers.add_parser(
        "single",
        help="Single acceptance sampling plan",
        description="A single sample of size n is inspected. If it contains more errors than the "
        "critical value c, the lot is rejected, otherwise it is accepted.",
    )

    add_distribution_arg(parser)
    add_quality_level_args(parser)
    add_risk_args(parser)
    add_lot_size_arg(parser)
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=DEFAULT_LIMIT,
        help="Largest sample size to search for, binomial only (default: %(default)s)",
    )
    add_output_args(parser)

    parser.set_defaults(func=run)

    return parser


def run(args: argparse.Namespace):
    payload = compute_single(
        distribution=args.distribution,
        p_a=args.p_a,
        p_r=args.p_r,
        alpha=args.alpha,
        beta=args.beta,
        lot_size=args.lot_size,
        limit=args.limit,
    )

    lines = [f"Single Sampling Plan {payload['distribution']}: n={payload['n']}, c={payload['c']}"]

    emit(payload, lines, args.json)
