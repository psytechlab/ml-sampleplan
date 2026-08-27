from dataclasses import asdict, dataclass, replace
from typing import Any, Dict, Optional, Tuple

from sampleplan.service import (
    AGRESTI_COULL,
    BINOMIAL,
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    EXACT,
    HYPERGEOMETRIC,
    MID_P,
)
from sampleplan.web.config import (
    DEFAULT_SEARCH_LIMIT,
    MAX_DOUBLE_RATIO,
    MAX_LOT_SIZE,
    MAX_SEARCH_LIMIT,
    MAX_SEQUENTIAL_CUTOFF,
    MAX_SEQUENTIAL_LOT_SIZE,
)


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str
    type: str = "number"
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    default: Any = None
    required: bool = False
    options: Tuple[str, ...] = ()
    depends_on_distribution: Optional[str] = None
    help: str = ""


@dataclass(frozen=True)
class FormSpec:
    label: str
    fields: Tuple[FieldSpec, ...]


PROBABILITY = {"minimum": 0, "maximum": 1, "step": 0.001}

DISTRIBUTION = FieldSpec(
    "distribution",
    "Distribution",
    type="select",
    default=BINOMIAL,
    required=True,
    options=(BINOMIAL, HYPERGEOMETRIC),
    help="Binomial samples with replacement; hypergeometric samples without replacement.",
)
LOT_SIZE = FieldSpec(
    "lot_size",
    "Lot size",
    minimum=1,
    maximum=MAX_LOT_SIZE,
    step=1,
    required=True,
    depends_on_distribution=HYPERGEOMETRIC,
    help="Size of the lot; required for the hypergeometric distribution.",
)
ALPHA = FieldSpec(
    "alpha",
    "Producer's risk (alpha)",
    default=DEFAULT_ALPHA,
    required=True,
    help="Probability of rejecting a lot that should have been accepted.",
    **PROBABILITY,
)
BETA = FieldSpec(
    "beta",
    "Consumer's risk (beta)",
    default=DEFAULT_BETA,
    required=True,
    help="Probability of accepting a lot that should have been rejected.",
    **PROBABILITY,
)
P_A = FieldSpec(
    "p_a",
    "Acceptable defect rate",
    default=0.01,
    required=True,
    help="Acceptable ratio of defective items in a lot.",
    **PROBABILITY,
)
P_R = FieldSpec(
    "p_r",
    "Rejectable defect rate",
    default=0.05,
    required=True,
    help="Unacceptable ratio of defective items in a lot.",
    **PROBABILITY,
)
LIMIT = FieldSpec(
    "limit",
    "Search limit",
    minimum=1,
    maximum=MAX_SEARCH_LIMIT,
    step=1,
    default=DEFAULT_SEARCH_LIMIT,
    required=True,
    depends_on_distribution=BINOMIAL,
    help="Largest sample size to search for.",
)
SEQUENTIAL_LOT_SIZE = replace(LOT_SIZE, maximum=MAX_SEQUENTIAL_LOT_SIZE)

FORMS: Dict[str, FormSpec] = {
    "ci": FormSpec(
        "Confidence interval",
        (
            DISTRIBUTION,
            FieldSpec("p0", "Assumed defect rate", default=0.01, required=True, **PROBABILITY),
            FieldSpec("ci_half_width", "CI half width", default=0.01, required=True, **PROBABILITY),
            ALPHA,
            LOT_SIZE,
            FieldSpec(
                "method",
                "Method",
                type="select",
                default=EXACT,
                required=True,
                options=(EXACT, MID_P, AGRESTI_COULL),
                help="Agresti-Coull is available for the binomial distribution only.",
            ),
        ),
    ),
    "single": FormSpec("Single sampling", (DISTRIBUTION, P_A, P_R, ALPHA, BETA, LOT_SIZE, LIMIT)),
    "double": FormSpec(
        "Double sampling",
        (
            DISTRIBUTION,
            P_A,
            P_R,
            ALPHA,
            BETA,
            LOT_SIZE,
            FieldSpec(
                "ratio",
                "Second-to-first sample ratio",
                minimum=1,
                maximum=MAX_DOUBLE_RATIO,
                step=1,
                default=1,
                required=True,
            ),
            FieldSpec(
                "p",
                "Defect rate for average sample size",
                help="Defaults to the acceptable defect rate.",
                **PROBABILITY,
            ),
            LIMIT,
        ),
    ),
    "sequential": FormSpec(
        "Sequential sampling",
        (
            DISTRIBUTION,
            P_A,
            P_R,
            ALPHA,
            BETA,
            SEQUENTIAL_LOT_SIZE,
            FieldSpec(
                "p",
                "Defect rate for average sample number",
                depends_on_distribution=BINOMIAL,
                help="Defaults to the rejectable defect rate.",
                **PROBABILITY,
            ),
            FieldSpec(
                "defects",
                "Defects in lot",
                minimum=0,
                step=1,
                required=True,
                depends_on_distribution=HYPERGEOMETRIC,
            ),
            FieldSpec(
                "cutoff",
                "Cutoff",
                minimum=1,
                maximum=MAX_SEQUENTIAL_CUTOFF,
                step=1,
                help=f"Leave blank to use the plan default; maximum: {MAX_SEQUENTIAL_CUTOFF}.",
            ),
            FieldSpec(
                "include_limits",
                "Show acceptance and rejection limits",
                type="checkbox",
                default=False,
            ),
        ),
    ),
}


def form_descriptions() -> Dict[str, Dict[str, Any]]:
    return {name: asdict(spec) for name, spec in FORMS.items()}
