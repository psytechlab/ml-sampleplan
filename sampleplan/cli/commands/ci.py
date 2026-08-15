import argparse

from sampleplan.cli.common import (
    BINOMIAL,
    HYPERGEOMETRIC,
    CliError,
    add_distribution_arg,
    add_lot_size_arg,
    add_output_args,
    add_risk_args,
    emit,
    probability,
    require_lot_size,
)
from sampleplan.confidence_interval import (
    sample_size_agresti_coull_binomial,
    sample_size_exact_binomial,
    sample_size_exact_hypergeometric,
    sample_size_exact_mid_point_binomial,
    sample_size_exact_mid_point_hypergeometric,
)

EXACT = "exact"
MID_P = "mid-p"
AGRESTI_COULL = "agresti-coull"


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
        choices=[EXACT, MID_P, AGRESTI_COULL],
        default=EXACT,
        help="Clopper-Pearson exact, exact with mid-P correction or the Agresti-Coull "
        "approximation (default: %(default)s)",
    )
    add_output_args(parser)

    parser.set_defaults(func=run)

    return parser


def run(args: argparse.Namespace):
    lot_size = require_lot_size(args)

    if args.method == EXACT:
        if args.distribution == BINOMIAL:
            n = sample_size_exact_binomial(args.p0, args.alpha, args.ci_half_width)
        else:
            n = sample_size_exact_hypergeometric(lot_size, args.p0, args.alpha, args.ci_half_width)
    elif args.method == MID_P:
        if args.distribution == BINOMIAL:
            n = sample_size_exact_mid_point_binomial(args.p0, args.alpha, args.ci_half_width)
        else:
            n = sample_size_exact_mid_point_hypergeometric(lot_size, args.p0, args.alpha, args.ci_half_width)
    else:
        if args.distribution == HYPERGEOMETRIC:
            raise CliError(f"--method {AGRESTI_COULL} is only implemented for the binomial distribution")

        n = sample_size_agresti_coull_binomial(args.p0, args.alpha, args.ci_half_width)

    payload = {
        "command": "ci",
        "distribution": args.distribution,
        "method": args.method,
        "p0": args.p0,
        "alpha": args.alpha,
        "ci_half_width": args.ci_half_width,
        "lot_size": lot_size,
        "n": n,
    }

    lines = [f"Confidence interval sample size ({args.distribution}, {args.method}): n={n}"]

    emit(payload, lines, args.json)
