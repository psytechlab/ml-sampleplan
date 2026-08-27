from typing import Any

import pytest

from sampleplan.service import (
    SamplePlanError,
    compute_ci,
    compute_double,
    compute_sequential,
    compute_single,
)


def assert_builtin(value: Any):
    if isinstance(value, dict):
        assert all(isinstance(key, str) for key in value)
        for item in value.values():
            assert_builtin(item)
    elif isinstance(value, list):
        for item in value:
            assert_builtin(item)
    else:
        assert value is None or type(value) in (bool, int, float, str)


@pytest.mark.parametrize(
    "result",
    [
        compute_ci("binomial", 0.01, 0.01),
        compute_single("binomial", 0.01, 0.05),
        compute_double("binomial", 0.01, 0.05),
        compute_sequential("binomial", 0.01, 0.05, cutoff=30, include_limits=True),
        compute_sequential(
            "hypergeometric",
            0.01,
            0.05,
            lot_size=1000,
            defects=4,
            cutoff=83,
            include_limits=True,
        ),
    ],
)
def test_compute_returns_only_builtin_types(result):
    assert_builtin(result)


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (lambda: compute_ci("binomial", 1.5, 0.01), "p0"),
        (lambda: compute_single("hypergeometric", 0.01, 0.05), "lot-size"),
        (
            lambda: compute_sequential("hypergeometric", 0.01, 0.05, lot_size=1000),
            "defects",
        ),
        (
            lambda: compute_sequential("hypergeometric", 0.01, 0.05, lot_size=100, defects=101),
            "cannot be larger",
        ),
        (lambda: compute_single("binomial", 0.05, 0.05), "has to be smaller"),
        (lambda: compute_single("binomial", 0.01, 0.05, alpha=0.8, beta=0.4), "1 - alpha"),
        (
            lambda: compute_sequential("binomial", 0.01, 0.05, cutoff=101, max_cutoff=100),
            "configured maximum",
        ),
        (
            lambda: compute_sequential("binomial", 0.01, 0.05, max_cutoff=1),
            "configured maximum",
        ),
    ],
)
def test_invalid_service_inputs_raise_sampleplan_error(call, message):
    with pytest.raises(SamplePlanError, match=message):
        call()


def test_calculation_value_error_becomes_sampleplan_error():
    with pytest.raises(SamplePlanError, match="Did not find a sample plan within lot_size=10"):
        compute_single("hypergeometric", 0.01, 0.05, lot_size=10)


def test_double_hypergeometric_rejects_a_plan_larger_than_the_lot():
    with pytest.raises(SamplePlanError, match="requires 121 items"):
        compute_double("hypergeometric", 0.01, 0.05, lot_size=100, ratio=10)
