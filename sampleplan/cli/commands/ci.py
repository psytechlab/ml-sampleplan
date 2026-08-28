import argparse

from sampleplan.cli.common import (
    add_distribution_arg,
    add_lot_size_arg,
    add_output_args,
    add_risk_args,
    emit,
    probability,
)
from sampleplan.service import CI_METHODS, EXACT, compute_ci


def register(subparsers):
    parser = subparsers.add_parser(
        "ci",
        help="Sample size for a confidence interval of a given half width",
        description="Computes the sample size needed so that the confidence interval around p0 "
        "has at most the given half width.",
    )

    add_distribution_arg(parser)
    parser.add_argument("--p0", type=probability, required=True, help="The assumed error rate")
    parser.add_argument(
        "--ci-half-width",
        type=probability,
        required=True,
        help="The size of the confidence interval in one direction",
    )
    add_risk_args(parser, with_beta=False)
    add_lot_size_arg(parser)
    parser.add_argument(
        "--method",
        choices=list(CI_METHODS),
        default=EXACT,
        help="Clopper-Pearson exact, exact with mid-P correction or the Agresti-Coull "
        "approximation (default: %(default)s)",
    )
    add_output_args(parser)

    parser.set_defaults(func=run)

    return parser


def run(args: argparse.Namespace):
    payload = compute_ci(
        distribution=args.distribution,
        p0=args.p0,
        ci_half_width=args.ci_half_width,
        alpha=args.alpha,
        lot_size=args.lot_size,
        method=args.method,
    )

    lines = [f"Confidence interval sample size ({payload['distribution']}, {payload['method']}): n={payload['n']}"]

    emit(payload, lines, args.json)
