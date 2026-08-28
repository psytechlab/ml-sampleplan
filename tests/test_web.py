import json

import pytest
from fastapi.testclient import TestClient

from sampleplan.acceptance_sampling import (
    BinomialSequentialSamplingPlan,
    DoubleSamplingPlan,
    HypergeometricSequentialSamplingPlan,
    SingleSamplingPlan,
)
from sampleplan.cli import main as cli_main
from sampleplan.confidence_interval import (
    sample_size_exact_binomial,
    sample_size_exact_hypergeometric,
)
from sampleplan.web.app import create_app
from sampleplan.web.config import (
    MAX_DOUBLE_RATIO,
    MAX_LOT_SIZE,
    MAX_SEARCH_LIMIT,
    MAX_SEQUENTIAL_CUTOFF,
    MAX_SEQUENTIAL_LOT_SIZE,
)

client = TestClient(create_app())


def expected_single(distribution, lot_size=None):
    if distribution == "binomial":
        plan = SingleSamplingPlan.binomial(0.01, 0.05, 0.05, 0.2)
    else:
        plan = SingleSamplingPlan.hypergeometric(0.01, 0.05, 0.05, 0.2, lot_size)
    return {"n": plan.n, "c": plan.c}


def expected_double(distribution, lot_size=None):
    if distribution == "binomial":
        plan = DoubleSamplingPlan.binomial(0.01, 0.05, 0.05, 0.2)
    else:
        plan = DoubleSamplingPlan.hypergeometric(0.01, 0.05, 0.05, 0.2, lot_size)
    return {
        "n": plan.n,
        "c1": plan.c1,
        "c2": plan.c2,
        "average_sample_size": plan.average_sample_size(0.01),
        "average_sample_size_curtailed": plan.average_sample_size_curtailed(0.01),
    }


def expected_sequential_binomial():
    plan = BinomialSequentialSamplingPlan(0.01, 0.05, 0.05, 0.2)
    return {
        "cutoff": 30,
        "average_sample_number": plan.average_sample_number(0.05),
        "average_sample_number_curtailed": plan.average_sample_with_cutoff(0.05, 30),
    }


def expected_sequential_hypergeometric():
    plan = HypergeometricSequentialSamplingPlan(0.01, 0.05, 0.05, 0.2, 1000)
    properties = plan.average_sample_number(4, 83)
    return {
        "cutoff": 83,
        "average_sample_number": properties.average_sample_number,
        "lower_limits": list(properties.region.lower_limits),
        "upper_limits": list(properties.region.upper_limits),
    }


@pytest.mark.parametrize(
    ("endpoint", "payload", "expected"),
    [
        (
            "ci",
            {"distribution": "binomial", "p0": 0.01, "ci_half_width": 0.01},
            lambda: {"n": sample_size_exact_binomial(0.01, 0.05, 0.01)},
        ),
        (
            "ci",
            {"distribution": "hypergeometric", "lot_size": 1000, "p0": 0.01, "ci_half_width": 0.01},
            lambda: {"n": sample_size_exact_hypergeometric(1000, 0.01, 0.05, 0.01)},
        ),
        (
            "single",
            {"distribution": "binomial", "p_a": 0.01, "p_r": 0.05},
            lambda: expected_single("binomial"),
        ),
        (
            "single",
            {"distribution": "hypergeometric", "lot_size": 1000, "p_a": 0.01, "p_r": 0.05},
            lambda: expected_single("hypergeometric", 1000),
        ),
        (
            "double",
            {"distribution": "binomial", "p_a": 0.01, "p_r": 0.05},
            lambda: expected_double("binomial"),
        ),
        (
            "double",
            {"distribution": "hypergeometric", "lot_size": 1000, "p_a": 0.01, "p_r": 0.05},
            lambda: expected_double("hypergeometric", 1000),
        ),
        (
            "sequential",
            {"distribution": "binomial", "p_a": 0.01, "p_r": 0.05, "cutoff": 30},
            expected_sequential_binomial,
        ),
        (
            "sequential",
            {
                "distribution": "hypergeometric",
                "lot_size": 1000,
                "p_a": 0.01,
                "p_r": 0.05,
                "defects": 4,
                "cutoff": 83,
                "include_limits": True,
            },
            expected_sequential_hypergeometric,
        ),
    ],
)
def test_calculation_endpoints(endpoint, payload, expected):
    response = client.post(f"/api/{endpoint}", json=payload)

    assert response.status_code == 200
    result = response.json()
    for key, value in expected().items():
        if isinstance(value, float):
            assert result[key] == pytest.approx(value)
        else:
            assert result[key] == value


def test_api_matches_cli_json(capsys):
    argv = ["single", "-d", "binomial", "--p-a", "0.01", "--p-r", "0.05", "--json"]
    assert cli_main(argv) == 0
    cli_result = json.loads(capsys.readouterr().out)

    response = client.post(
        "/api/single",
        json={"distribution": "binomial", "p_a": 0.01, "p_r": 0.05},
    )

    assert response.status_code == 200
    assert response.json() == cli_result


@pytest.mark.parametrize(
    ("endpoint", "payload"),
    [
        ("ci", {"distribution": "binomial", "p0": 1.5, "ci_half_width": 0.01}),
        ("single", {"distribution": "hypergeometric", "p_a": 0.01, "p_r": 0.05}),
        (
            "sequential",
            {"distribution": "hypergeometric", "lot_size": 1000, "p_a": 0.01, "p_r": 0.05},
        ),
        (
            "single",
            {"distribution": "hypergeometric", "lot_size": 1_000_001, "p_a": 0.01, "p_r": 0.05},
        ),
        (
            "sequential",
            {"distribution": "hypergeometric", "lot_size": 20_001, "p_a": 0.01, "p_r": 0.05, "defects": 1},
        ),
        (
            "single",
            {"distribution": "binomial", "p_a": 0.01, "p_r": 0.05, "limit": MAX_SEARCH_LIMIT + 1},
        ),
        (
            "sequential",
            {"distribution": "binomial", "p_a": 0.01, "p_r": 0.05, "cutoff": MAX_SEQUENTIAL_CUTOFF + 1},
        ),
        (
            "double",
            {"distribution": "binomial", "p_a": 0.01, "p_r": 0.05, "ratio": MAX_DOUBLE_RATIO + 1},
        ),
    ],
)
def test_invalid_requests_return_422(endpoint, payload):
    response = client.post(f"/api/{endpoint}", json=payload)

    assert response.status_code == 422


def test_impossible_plan_returns_explanatory_422():
    response = client.post(
        "/api/single",
        json={"distribution": "hypergeometric", "lot_size": 10, "p_a": 0.01, "p_r": 0.05},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "Did not find a sample plan within lot_size=10; "
            "increase lot_size or relax the quality levels or risk limits"
        )
    }


def test_double_hypergeometric_plan_larger_than_lot_returns_422():
    response = client.post(
        "/api/double",
        json={"distribution": "hypergeometric", "lot_size": 100, "p_a": 0.01, "p_r": 0.05, "ratio": 10},
    )

    assert response.status_code == 422
    assert "requires 121 items" in response.json()["detail"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"distribution": "binomial", "p_a": 0.05, "p_r": 0.05}, "p_a (0.05) has to be smaller"),
        (
            {"distribution": "binomial", "p_a": 0.01, "p_r": 0.05, "alpha": 0.8, "beta": 0.4},
            "beta (0.4) has to be smaller than 1 - alpha",
        ),
    ],
)
def test_related_plan_parameters_return_explanatory_422(payload, message):
    response = client.post("/api/single", json=payload)

    assert response.status_code == 422
    assert message in response.json()["detail"]


def test_health():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"]


def test_index():
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "sampleplan" in response.text


def test_forms_include_all_methods():
    response = client.get("/api/forms")

    assert response.status_code == 200
    forms = response.json()
    assert set(forms) == {"ci", "single", "double", "sequential"}

    fields = {
        method: {field["name"]: field for field in description["fields"]} for method, description in forms.items()
    }
    assert fields["single"]["lot_size"]["maximum"] == MAX_LOT_SIZE
    assert fields["single"]["limit"]["maximum"] == MAX_SEARCH_LIMIT
    assert fields["double"]["ratio"]["maximum"] == MAX_DOUBLE_RATIO
    assert fields["sequential"]["lot_size"]["maximum"] == MAX_SEQUENTIAL_LOT_SIZE
    assert fields["sequential"]["cutoff"]["maximum"] == MAX_SEQUENTIAL_CUTOFF
