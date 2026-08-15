import argparse

from sampleplan.acceptance_sampling import SingleSamplingPlan
from sampleplan.cli.common import (
    BINOMIAL,
    add_distribution_arg,
    add_lot_size_arg,
    add_output_args,
    add_quality_level_args,
    add_risk_args,
    emit,
    positive_int,
    require_lot_size,
)


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
        default=100_000,
        help="Largest sample size to search for, binomial only (default: %(default)s)",
    )
    add_output_args(parser)

    parser.set_defaults(func=run)

    return parser


def build_plan(args: argparse.Namespace, lot_size) -> SingleSamplingPlan:
    if args.distribution == BINOMIAL:
        return SingleSamplingPlan.binomial(args.p_a, args.p_r, args.alpha, args.beta, args.limit)

    return SingleSamplingPlan.hypergeometric(args.p_a, args.p_r, args.alpha, args.beta, lot_size)


def run(args: argparse.Namespace):
    lot_size = require_lot_size(args)
    plan = build_plan(args, lot_size)

    payload = {
        "command": "single",
        "distribution": args.distribution,
        "p_a": args.p_a,
        "p_r": args.p_r,
        "alpha": args.alpha,
        "beta": args.beta,
        "lot_size": lot_size,
        "n": plan.n,
        "c": plan.c,
    }

    lines = [f"Single Sampling Plan {args.distribution}: n={plan.n}, c={plan.c}"]

    emit(payload, lines, args.json)
