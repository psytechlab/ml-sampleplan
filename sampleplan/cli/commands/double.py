import argparse

from sampleplan.acceptance_sampling import DoubleSamplingPlan
from sampleplan.cli.common import (
    BINOMIAL,
    add_distribution_arg,
    add_lot_size_arg,
    add_output_args,
    add_quality_level_args,
    add_risk_args,
    emit,
    positive_int,
    probability,
    require_lot_size,
)


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
        default=100_000,
        help="Largest sample size to search for, binomial only (default: %(default)s)",
    )
    add_output_args(parser)

    parser.set_defaults(func=run)

    return parser


def run(args: argparse.Namespace):
    lot_size = require_lot_size(args)

    if args.distribution == BINOMIAL:
        plan = DoubleSamplingPlan.binomial(args.p_a, args.p_r, args.alpha, args.beta, args.ratio, args.limit)
    else:
        plan = DoubleSamplingPlan.hypergeometric(args.p_a, args.p_r, args.alpha, args.beta, lot_size, args.ratio)

    p = args.p if args.p is not None else args.p_a
    asn = plan.average_sample_size(p)
    asn_curtailed = plan.average_sample_size_curtailed(p)

    payload = {
        "command": "double",
        "distribution": args.distribution,
        "p_a": args.p_a,
        "p_r": args.p_r,
        "alpha": args.alpha,
        "beta": args.beta,
        "lot_size": lot_size,
        "p": p,
        "n": plan.n,
        "c1": plan.c1,
        "c2": plan.c2,
        "r": plan.r,
        "average_sample_size": asn,
        "average_sample_size_curtailed": asn_curtailed,
    }

    lines = [
        f"Double Sampling Plan {args.distribution}: n1={plan.n}, n2={plan.n * plan.r}, c1={plan.c1}, c2={plan.c2}",
        f"Average sample size at p={p}: full={asn:.4f}, curtailed={asn_curtailed:.4f}",
    ]

    emit(payload, lines, args.json)
