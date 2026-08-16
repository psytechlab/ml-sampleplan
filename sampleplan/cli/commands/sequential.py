import argparse

from sampleplan.acceptance_sampling import (
    BinomialSequentialSamplingPlan,
    HypergeometricSequentialSamplingPlan,
    SingleSamplingPlan,
)
from sampleplan.acceptance_sampling.sequential import SequentialSamplingPlanRegion
from sampleplan.cli.common import (
    BINOMIAL,
    CliError,
    add_distribution_arg,
    add_lot_size_arg,
    add_output_args,
    add_quality_level_args,
    add_risk_args,
    emit,
    non_negative_int,
    positive_int,
    probability,
    require_lot_size,
)

BINOMIAL_CUTOFF_FACTOR = 3


def register(subparsers):
    parser = subparsers.add_parser(
        "sequential",
        help="Sequential acceptance sampling plan",
        description="Instances are inspected one by one; after each step it is decided whether to "
        "continue or to stop and accept or reject. The plan is truncated at the given cutoff.",
    )

    add_distribution_arg(parser)
    add_quality_level_args(parser)
    add_risk_args(parser)
    add_lot_size_arg(parser)
    parser.add_argument(
        "--p",
        type=probability,
        help="True error rate to compute the average sample number for, binomial only (default: --p-r)",
    )
    parser.add_argument(
        "--defects",
        type=non_negative_int,
        help="Number of defects in the lot, required for the hypergeometric distribution",
    )
    parser.add_argument(
        "--cutoff",
        type=positive_int,
        help="Truncate the plan at this sample size (default: 3x the single sampling plan sample "
        "size for binomial, the single sampling plan sample size for hypergeometric)",
    )
    parser.add_argument(
        "--print-limits",
        action="store_true",
        help="Also print the acceptance and rejection limits for every step",
    )
    add_output_args(parser)

    parser.set_defaults(func=run)

    return parser


def _limit_lines(region: SequentialSamplingPlanRegion):
    lines = ["", "Items inspected\tAccept if num errors <\tReject if num errors >"]

    for i, (lower, upper) in enumerate(zip(region.lower_limits, region.upper_limits)):
        lines.append(f"{i}\t\t{'*' if lower is None else lower}\t\t\t{'*' if upper is None else upper}")

    return lines


def _run_binomial(args: argparse.Namespace):
    plan = BinomialSequentialSamplingPlan(args.p_a, args.p_r, args.alpha, args.beta)

    p = args.p if args.p is not None else args.p_r

    cutoff = args.cutoff
    if cutoff is None:
        ssp = SingleSamplingPlan.binomial(args.p_a, args.p_r, args.alpha, args.beta)
        cutoff = ssp.n * BINOMIAL_CUTOFF_FACTOR

    asn = plan.average_sample_number(p)
    asn_curtailed = plan.average_sample_with_cutoff(p, cutoff)

    payload = {
        "h1": plan.h1,
        "h2": plan.h2,
        "s": plan.s,
        "p": p,
        "cutoff": cutoff,
        "average_sample_number": asn,
        "average_sample_number_curtailed": asn_curtailed,
    }

    lines = [
        f"Sequential Sampling Plan binomial: h1={plan.h1:.4f}, h2={plan.h2:.4f}, s={plan.s:.4f}",
        f"Average sample number at p={p}: full={asn:.4f}, curtailed at {cutoff}={asn_curtailed:.4f}",
    ]

    region = plan.compute_region(cutoff + 1) if args.print_limits else None

    return payload, lines, region


def _run_hypergeometric(args: argparse.Namespace, lot_size: int):
    if args.defects is None:
        raise CliError("--defects is required for the hypergeometric distribution")

    if args.defects > lot_size:
        raise CliError(f"--defects ({args.defects}) cannot be larger than --lot-size ({lot_size})")

    plan = HypergeometricSequentialSamplingPlan(args.p_a, args.p_r, args.alpha, args.beta, lot_size)

    cutoff = args.cutoff
    if cutoff is None:
        ssp = SingleSamplingPlan.hypergeometric(args.p_a, args.p_r, args.alpha, args.beta, lot_size)
        cutoff = ssp.n

    if cutoff > lot_size:
        raise CliError(f"--cutoff ({cutoff}) cannot be larger than --lot-size ({lot_size})")

    properties = plan.average_sample_number(args.defects, cutoff)
    asn = properties.average_sample_number

    payload = {
        "lot_size": lot_size,
        "defects": args.defects,
        "cutoff": cutoff,
        "average_sample_number": asn,
    }

    lines = [
        f"Sequential Sampling Plan hypergeometric: lot_size={lot_size}, cutoff={cutoff}",
        f"Average sample number at {args.defects} defects in the lot: {asn:.4f}",
    ]

    return payload, lines, properties.region if args.print_limits else None


def run(args: argparse.Namespace):
    lot_size = require_lot_size(args)

    if args.distribution == BINOMIAL:
        payload, lines, region = _run_binomial(args)
    else:
        payload, lines, region = _run_hypergeometric(args, lot_size)

    payload = {
        "command": "sequential",
        "distribution": args.distribution,
        "p_a": args.p_a,
        "p_r": args.p_r,
        "alpha": args.alpha,
        "beta": args.beta,
        **payload,
    }

    if region is not None:
        payload["lower_limits"] = list(region.lower_limits)
        payload["upper_limits"] = list(region.upper_limits)
        lines += _limit_lines(region)

    emit(payload, lines, args.json)
