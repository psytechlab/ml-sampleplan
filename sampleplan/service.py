from functools import wraps
from typing import Any, Dict, Optional, Tuple

import numpy as np

from sampleplan.acceptance_sampling import (
    BinomialSequentialSamplingPlan,
    DoubleSamplingPlan,
    HypergeometricSequentialSamplingPlan,
    SingleSamplingPlan,
)
from sampleplan.acceptance_sampling.sequential import SequentialSamplingPlanRegion
from sampleplan.confidence_interval import (
    sample_size_agresti_coull_binomial,
    sample_size_exact_binomial,
    sample_size_exact_hypergeometric,
    sample_size_exact_mid_point_binomial,
    sample_size_exact_mid_point_hypergeometric,
)

BINOMIAL = "binomial"
HYPERGEOMETRIC = "hypergeometric"
DISTRIBUTIONS = (BINOMIAL, HYPERGEOMETRIC)

EXACT = "exact"
MID_P = "mid-p"
AGRESTI_COULL = "agresti-coull"
CI_METHODS = (EXACT, MID_P, AGRESTI_COULL)

DEFAULT_ALPHA = 0.05
DEFAULT_BETA = 0.2
DEFAULT_LIMIT = 100_000
BINOMIAL_CUTOFF_FACTOR = 3


class SamplePlanError(Exception):
    """Raised for invalid input, with a message meant to be shown to the user as is."""


def _raise_hypergeometric_plan_error(error: ValueError, lot_size: int):
    """Rewords the numerical layer's binomial-oriented search-limit error."""

    if str(error).startswith("Did not find sample plan"):
        raise SamplePlanError(
            f"Did not find a sample plan within lot_size={lot_size}; "
            "increase lot_size or relax the quality levels or risk limits"
        ) from error

    raise error


def _translate_calculation_errors(function):
    """Turns errors from the numerical layer into the public service error type."""

    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except (ValueError, AssertionError) as error:
            message = str(error) or "The calculation could not be completed with these inputs"
            raise SamplePlanError(message) from error

    return wrapped


def validate_probability(name: str, value: float) -> float:
    if not 0.0 < value < 1.0:
        raise SamplePlanError(f"{name} ({value}) has to be strictly between 0 and 1")

    return value


def validate_positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value <= 0:
        raise SamplePlanError(f"{name} ({value}) has to be larger than 0")

    return int(value)


def validate_non_negative_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0:
        raise SamplePlanError(f"{name} ({value}) has to be 0 or larger")

    return int(value)


def to_builtin(value: Any) -> Any:
    """Recursively replaces numpy scalars with their python equivalents so results are serializable."""

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, dict):
        return {key: to_builtin(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_builtin(item) for item in value]

    return value


def _check_distribution(distribution: str):
    if distribution not in DISTRIBUTIONS:
        raise SamplePlanError(f"unknown distribution '{distribution}', expected one of {', '.join(DISTRIBUTIONS)}")


def _require_lot_size(distribution: str, lot_size: Optional[int]) -> Optional[int]:
    _check_distribution(distribution)

    if distribution == HYPERGEOMETRIC and lot_size is None:
        raise SamplePlanError("--lot-size is required for the hypergeometric distribution")

    if lot_size is not None:
        lot_size = validate_positive_int("lot_size", lot_size)

    return lot_size


def _validate_plan_inputs(p_a: float, p_r: float, alpha: float, beta: float):
    validate_probability("p_a", p_a)
    validate_probability("p_r", p_r)
    validate_probability("alpha", alpha)
    validate_probability("beta", beta)

    if p_a >= p_r:
        raise SamplePlanError(f"p_a ({p_a}) has to be smaller than p_r ({p_r})")

    if beta >= 1 - alpha:
        raise SamplePlanError(f"beta ({beta}) has to be smaller than 1 - alpha ({1 - alpha})")


@_translate_calculation_errors
def compute_ci(
    distribution: str,
    p0: float,
    ci_half_width: float,
    alpha: float = DEFAULT_ALPHA,
    lot_size: Optional[int] = None,
    method: str = EXACT,
) -> Dict[str, Any]:
    lot_size = _require_lot_size(distribution, lot_size)
    validate_probability("p0", p0)
    validate_probability("ci_half_width", ci_half_width)
    validate_probability("alpha", alpha)

    if method not in CI_METHODS:
        raise SamplePlanError(f"unknown method '{method}', expected one of {', '.join(CI_METHODS)}")

    if method == EXACT:
        if distribution == BINOMIAL:
            n = sample_size_exact_binomial(p0, alpha, ci_half_width)
        else:
            n = sample_size_exact_hypergeometric(lot_size, p0, alpha, ci_half_width)
    elif method == MID_P:
        if distribution == BINOMIAL:
            n = sample_size_exact_mid_point_binomial(p0, alpha, ci_half_width)
        else:
            n = sample_size_exact_mid_point_hypergeometric(lot_size, p0, alpha, ci_half_width)
    else:
        if distribution == HYPERGEOMETRIC:
            raise SamplePlanError(f"--method {AGRESTI_COULL} is only implemented for the binomial distribution")

        n = sample_size_agresti_coull_binomial(p0, alpha, ci_half_width)

    return to_builtin(
        {
            "command": "ci",
            "distribution": distribution,
            "method": method,
            "p0": p0,
            "alpha": alpha,
            "ci_half_width": ci_half_width,
            "lot_size": lot_size,
            "n": n,
        }
    )


@_translate_calculation_errors
def compute_single(
    distribution: str,
    p_a: float,
    p_r: float,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    lot_size: Optional[int] = None,
    limit: int = DEFAULT_LIMIT,
) -> Dict[str, Any]:
    lot_size = _require_lot_size(distribution, lot_size)
    _validate_plan_inputs(p_a, p_r, alpha, beta)
    limit = validate_positive_int("limit", limit)

    if distribution == BINOMIAL:
        plan = SingleSamplingPlan.binomial(p_a, p_r, alpha, beta, limit)
    else:
        try:
            plan = SingleSamplingPlan.hypergeometric(p_a, p_r, alpha, beta, lot_size)
        except ValueError as error:
            _raise_hypergeometric_plan_error(error, lot_size)

    return to_builtin(
        {
            "command": "single",
            "distribution": distribution,
            "p_a": p_a,
            "p_r": p_r,
            "alpha": alpha,
            "beta": beta,
            "lot_size": lot_size,
            "n": plan.n,
            "c": plan.c,
        }
    )


@_translate_calculation_errors
def compute_double(
    distribution: str,
    p_a: float,
    p_r: float,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    lot_size: Optional[int] = None,
    ratio: int = 1,
    p: Optional[float] = None,
    limit: int = DEFAULT_LIMIT,
) -> Dict[str, Any]:
    lot_size = _require_lot_size(distribution, lot_size)
    _validate_plan_inputs(p_a, p_r, alpha, beta)
    ratio = validate_positive_int("ratio", ratio)
    limit = validate_positive_int("limit", limit)

    if p is not None:
        validate_probability("p", p)

    if distribution == BINOMIAL:
        plan = DoubleSamplingPlan.binomial(p_a, p_r, alpha, beta, ratio, limit)
    else:
        try:
            plan = DoubleSamplingPlan.hypergeometric(p_a, p_r, alpha, beta, lot_size, ratio)
        except ValueError as error:
            _raise_hypergeometric_plan_error(error, lot_size)

        total_sample_size = plan.n * (plan.r + 1)
        if total_sample_size > lot_size:
            raise SamplePlanError(
                f"double sampling plan requires {total_sample_size} items, "
                f"which is larger than lot_size ({lot_size}); reduce ratio or increase lot_size"
            )

    if p is None:
        p = p_a

    return to_builtin(
        {
            "command": "double",
            "distribution": distribution,
            "p_a": p_a,
            "p_r": p_r,
            "alpha": alpha,
            "beta": beta,
            "lot_size": lot_size,
            "p": p,
            "n": plan.n,
            "c1": plan.c1,
            "c2": plan.c2,
            "r": plan.r,
            "average_sample_size": plan.average_sample_size(p),
            "average_sample_size_curtailed": plan.average_sample_size_curtailed(p),
        }
    )


def _sequential_binomial(
    p_a: float,
    p_r: float,
    alpha: float,
    beta: float,
    p: Optional[float],
    cutoff: Optional[int],
    include_limits: bool,
    max_cutoff: Optional[int],
) -> Tuple[Dict[str, Any], Optional[SequentialSamplingPlanRegion]]:
    plan = BinomialSequentialSamplingPlan(p_a, p_r, alpha, beta)

    if p is None:
        p = p_r

    if cutoff is None:
        cutoff = SingleSamplingPlan.binomial(p_a, p_r, alpha, beta).n * BINOMIAL_CUTOFF_FACTOR

    if max_cutoff is not None and cutoff > max_cutoff:
        raise SamplePlanError(f"cutoff ({cutoff}) cannot be larger than the configured maximum ({max_cutoff})")

    payload = {
        "h1": plan.h1,
        "h2": plan.h2,
        "s": plan.s,
        "p": p,
        "cutoff": cutoff,
        "average_sample_number": plan.average_sample_number(p),
        "average_sample_number_curtailed": plan.average_sample_with_cutoff(p, cutoff),
    }

    region = plan.compute_region(cutoff + 1) if include_limits else None

    return payload, region


def _sequential_hypergeometric(
    p_a: float,
    p_r: float,
    alpha: float,
    beta: float,
    lot_size: int,
    defects: Optional[int],
    cutoff: Optional[int],
    include_limits: bool,
    max_cutoff: Optional[int],
) -> Tuple[Dict[str, Any], Optional[SequentialSamplingPlanRegion]]:
    if defects is None:
        raise SamplePlanError("--defects is required for the hypergeometric distribution")

    defects = validate_non_negative_int("defects", defects)

    if defects > lot_size:
        raise SamplePlanError(f"--defects ({defects}) cannot be larger than --lot-size ({lot_size})")

    plan = HypergeometricSequentialSamplingPlan(p_a, p_r, alpha, beta, lot_size)

    if cutoff is None:
        try:
            cutoff = SingleSamplingPlan.hypergeometric(p_a, p_r, alpha, beta, lot_size).n
        except ValueError as error:
            _raise_hypergeometric_plan_error(error, lot_size)

    if cutoff > lot_size:
        raise SamplePlanError(f"--cutoff ({cutoff}) cannot be larger than --lot-size ({lot_size})")

    if max_cutoff is not None and cutoff > max_cutoff:
        raise SamplePlanError(f"cutoff ({cutoff}) cannot be larger than the configured maximum ({max_cutoff})")

    properties = plan.average_sample_number(defects, cutoff)

    payload = {
        "lot_size": lot_size,
        "defects": defects,
        "cutoff": cutoff,
        "average_sample_number": properties.average_sample_number,
    }

    return payload, properties.region if include_limits else None


@_translate_calculation_errors
def compute_sequential(
    distribution: str,
    p_a: float,
    p_r: float,
    alpha: float = DEFAULT_ALPHA,
    beta: float = DEFAULT_BETA,
    lot_size: Optional[int] = None,
    p: Optional[float] = None,
    defects: Optional[int] = None,
    cutoff: Optional[int] = None,
    include_limits: bool = False,
    max_cutoff: Optional[int] = None,
) -> Dict[str, Any]:
    lot_size = _require_lot_size(distribution, lot_size)
    _validate_plan_inputs(p_a, p_r, alpha, beta)

    if p is not None:
        validate_probability("p", p)

    if cutoff is not None:
        cutoff = validate_positive_int("cutoff", cutoff)

    if max_cutoff is not None:
        max_cutoff = validate_positive_int("max_cutoff", max_cutoff)

    if distribution == BINOMIAL:
        payload, region = _sequential_binomial(p_a, p_r, alpha, beta, p, cutoff, include_limits, max_cutoff)
    else:
        payload, region = _sequential_hypergeometric(
            p_a, p_r, alpha, beta, lot_size, defects, cutoff, include_limits, max_cutoff
        )

    payload = {
        "command": "sequential",
        "distribution": distribution,
        "p_a": p_a,
        "p_r": p_r,
        "alpha": alpha,
        "beta": beta,
        **payload,
    }

    if region is not None:
        payload["lower_limits"] = list(region.lower_limits)
        payload["upper_limits"] = list(region.upper_limits)

    return to_builtin(payload)
