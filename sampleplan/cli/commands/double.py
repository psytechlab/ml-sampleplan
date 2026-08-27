import argparse

from sampleplan.cli.common import (
    add_distribution_arg,
    add_lot_size_arg,
    add_output_args,
    add_quality_level_args,
    add_risk_args,
    emit,
    positive_int,
    probability,
)
from sampleplan.service import DEFAULT_LIMIT, compute_double


def register(subparsers):
    parser = subparsers.add_parser(
        "double",
        help="Double acceptance sampling plan",
        description="A first sample of size n1 is inspected; the lot is accepted if it contains at "
        "most c1 errors and rejected if it contains more than c2. Otherwise a second sample is "
        "taken and the lot is rejected if both samples combined contain more than c2 errors.",
    )

    add_distribution_arg(parser)
    add_quality_level_args(parser)
    add_risk_args(parser)
    add_lot_size_arg(parser)
    parser.add_argument(
        "-r",
        "--ratio",
        type=positive_int,
        default=1,
        help="Ratio between the second and the first sample size, n2 = r * n1 (default: %(default)s)",
    )
    parser.add_argument(
        "--p",
        type=probability,
        help="Error rate to compute the average sample number for (default: --p-a)",
    )
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
    payload = compute_double(
        distribution=args.distribution,
        p_a=args.p_a,
        p_r=args.p_r,
        alpha=args.alpha,
        beta=args.beta,
        lot_size=args.lot_size,
        ratio=args.ratio,
        p=args.p,
        limit=args.limit,
    )

    n, r = payload["n"], payload["r"]

    lines = [
        f"Double Sampling Plan {payload['distribution']}: n1={n}, n2={n * r}, c1={payload['c1']}, c2={payload['c2']}",
        f"Average sample size at p={payload['p']}: full={payload['average_sample_size']:.4f}, "
        f"curtailed={payload['average_sample_size_curtailed']:.4f}",
    ]

    emit(payload, lines, args.json)
