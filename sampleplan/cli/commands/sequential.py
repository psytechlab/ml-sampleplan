import argparse
from typing import Any, Dict, List

from sampleplan.cli.common import (
    add_distribution_arg,
    add_lot_size_arg,
    add_output_args,
    add_quality_level_args,
    add_risk_args,
    emit,
    non_negative_int,
    positive_int,
    probability,
)
from sampleplan.service import BINOMIAL, compute_sequential


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


def _limit_lines(payload: Dict[str, Any]) -> List[str]:
    lines = ["", "Items inspected\tAccept if num errors <\tReject if num errors >"]

    for i, (lower, upper) in enumerate(zip(payload["lower_limits"], payload["upper_limits"])):
        lines.append(f"{i}\t\t{'*' if lower is None else lower}\t\t\t{'*' if upper is None else upper}")

    return lines


def _summary_lines(payload: Dict[str, Any]) -> List[str]:
    asn = payload["average_sample_number"]

    if payload["distribution"] == BINOMIAL:
        return [
            f"Sequential Sampling Plan binomial: h1={payload['h1']:.4f}, h2={payload['h2']:.4f}, s={payload['s']:.4f}",
            f"Average sample number at p={payload['p']}: full={asn:.4f}, "
            f"curtailed at {payload['cutoff']}={payload['average_sample_number_curtailed']:.4f}",
        ]

    return [
        f"Sequential Sampling Plan hypergeometric: lot_size={payload['lot_size']}, cutoff={payload['cutoff']}",
        f"Average sample number at {payload['defects']} defects in the lot: {asn:.4f}",
    ]


def run(args: argparse.Namespace):
    payload = compute_sequential(
        distribution=args.distribution,
        p_a=args.p_a,
        p_r=args.p_r,
        alpha=args.alpha,
        beta=args.beta,
        lot_size=args.lot_size,
        p=args.p,
        defects=args.defects,
        cutoff=args.cutoff,
        include_limits=args.print_limits,
    )

    lines = _summary_lines(payload)

    if args.print_limits:
        lines += _limit_lines(payload)

    emit(payload, lines, args.json)
