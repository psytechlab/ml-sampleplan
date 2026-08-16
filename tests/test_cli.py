import json
from typing import List

import pytest

from sampleplan.acceptance_sampling import (
    DoubleSamplingPlan,
    HypergeometricSequentialSamplingPlan,
    SingleSamplingPlan,
)
from sampleplan.cli import main
from sampleplan.confidence_interval import (
    sample_size_exact_binomial,
    sample_size_exact_hypergeometric,
)

BINOMIAL_PLAN_ARGS = ["--p-a", "0.01", "--p-r", "0.05", "--alpha", "0.05", "--beta", "0.2"]
HYPERGEOMETRIC_PLAN_ARGS = BINOMIAL_PLAN_ARGS + ["--lot-size", "1000"]


def run_json(capsys, argv: List[str]) -> dict:
    assert main(argv + ["--json"]) == 0
    return json.loads(capsys.readouterr().out)


def test_ci_binomial(capsys):
    result = run_json(capsys, ["ci", "-d", "binomial", "--p0", "0.01", "--alpha", "0.05", "--ci-half-width", "0.01"])

    assert result["n"] == sample_size_exact_binomial(0.01, 0.05, 0.01)


def test_ci_hypergeometric(capsys):
    result = run_json(
        capsys,
        ["ci", "-d", "hypergeometric", "--lot-size", "1000", "--p0", "0.01", "--ci-half-width", "0.01"],
    )

    assert result["n"] == sample_size_exact_hypergeometric(1000, 0.01, 0.05, 0.01)


@pytest.mark.parametrize("method", ["exact", "mid-p", "agresti-coull"])
def test_ci_methods_binomial(capsys, method: str):
    result = run_json(
        capsys,
        ["ci", "-d", "binomial", "--p0", "0.01", "--ci-half-width", "0.01", "--method", method],
    )

    assert result["n"] > 0


def test_ci_agresti_coull_rejects_hypergeometric(capsys):
    with pytest.raises(SystemExit) as e:
        main(
            [
                "ci",
                "-d",
                "hypergeometric",
                "--lot-size",
                "1000",
                "--p0",
                "0.01",
                "--ci-half-width",
                "0.01",
                "--method",
                "agresti-coull",
            ]
        )

    assert e.value.code == 2


def test_single_binomial(capsys):
    result = run_json(capsys, ["single", "-d", "binomial"] + BINOMIAL_PLAN_ARGS)
    expected = SingleSamplingPlan.binomial(0.01, 0.05, 0.05, 0.2)

    assert result["n"] == expected.n
    assert result["c"] == expected.c


def test_single_hypergeometric(capsys):
    result = run_json(capsys, ["single", "-d", "hypergeometric"] + HYPERGEOMETRIC_PLAN_ARGS)
    expected = SingleSamplingPlan.hypergeometric(0.01, 0.05, 0.05, 0.2, 1000)

    assert result["n"] == expected.n
    assert result["c"] == expected.c


def test_double_binomial(capsys):
    result = run_json(capsys, ["double", "-d", "binomial"] + BINOMIAL_PLAN_ARGS)
    expected = DoubleSamplingPlan.binomial(0.01, 0.05, 0.05, 0.2)

    assert result["n"] == expected.n
    assert result["c1"] == expected.c1
    assert result["c2"] == expected.c2
    assert result["average_sample_size"] == pytest.approx(expected.average_sample_size(0.01))
    assert result["average_sample_size_curtailed"] == pytest.approx(expected.average_sample_size_curtailed(0.01))


def test_double_hypergeometric(capsys):
    result = run_json(capsys, ["double", "-d", "hypergeometric"] + HYPERGEOMETRIC_PLAN_ARGS)
    expected = DoubleSamplingPlan.hypergeometric(0.01, 0.05, 0.05, 0.2, 1000)

    assert result["n"] == expected.n
    assert result["c1"] == expected.c1
    assert result["c2"] == expected.c2


def test_sequential_binomial(capsys):
    result = run_json(capsys, ["sequential", "-d", "binomial", "--p", "0.07"] + BINOMIAL_PLAN_ARGS)

    assert result["cutoff"] == SingleSamplingPlan.binomial(0.01, 0.05, 0.05, 0.2).n * 3
    assert result["average_sample_number"] > 0
    assert result["average_sample_number_curtailed"] > 0


def test_sequential_hypergeometric(capsys):
    result = run_json(
        capsys,
        ["sequential", "-d", "hypergeometric", "--defects", "4", "--print-limits"] + HYPERGEOMETRIC_PLAN_ARGS,
    )

    cutoff = SingleSamplingPlan.hypergeometric(0.01, 0.05, 0.05, 0.2, 1000).n
    plan = HypergeometricSequentialSamplingPlan(0.01, 0.05, 0.05, 0.2, 1000)

    assert result["cutoff"] == cutoff
    assert result["average_sample_number"] == pytest.approx(plan.average_sample_number(4, cutoff).average_sample_number)
    assert len(result["lower_limits"]) == cutoff + 1
    assert len(result["upper_limits"]) == cutoff + 1


def test_sequential_hypergeometric_requires_defects():
    with pytest.raises(SystemExit) as e:
        main(["sequential", "-d", "hypergeometric"] + HYPERGEOMETRIC_PLAN_ARGS)

    assert e.value.code == 2


def test_plain_text_output(capsys):
    assert main(["single", "-d", "binomial"] + BINOMIAL_PLAN_ARGS) == 0

    out = capsys.readouterr().out
    assert "Single Sampling Plan binomial" in out
    assert "n=" in out and "c=" in out


@pytest.mark.parametrize(
    "argv",
    [
        ["single", "-d", "hypergeometric", "--p-a", "0.01", "--p-r", "0.05"],  # missing --lot-size
        ["ci", "-d", "binomial", "--p0", "1.5", "--ci-half-width", "0.01"],  # p0 out of range
        ["ci", "-d", "binomial", "--ci-half-width", "0.01"],  # missing --p0
        ["single", "-d", "poisson", "--p-a", "0.01", "--p-r", "0.05"],  # unknown distribution
        [],  # no command
    ],
)
def test_invalid_invocations_exit_nonzero(argv: List[str]):
    with pytest.raises(SystemExit) as e:
        main(argv)

    assert e.value.code != 0
