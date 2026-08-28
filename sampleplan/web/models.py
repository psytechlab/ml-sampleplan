from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sampleplan.service import DEFAULT_ALPHA, DEFAULT_BETA, EXACT
from sampleplan.web.config import (
    DEFAULT_SEARCH_LIMIT,
    MAX_DOUBLE_RATIO,
    MAX_LOT_SIZE,
    MAX_SEARCH_LIMIT,
    MAX_SEQUENTIAL_CUTOFF,
    MAX_SEQUENTIAL_LOT_SIZE,
)

Distribution = Literal["binomial", "hypergeometric"]
CiMethod = Literal["exact", "mid-p", "agresti-coull"]


Probability = Field(gt=0, lt=1)


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LotRequest(RequestModel):
    distribution: Distribution
    lot_size: Optional[int] = Field(default=None, gt=0, le=MAX_LOT_SIZE)


class CiRequest(LotRequest):
    p0: float = Probability
    ci_half_width: float = Probability
    alpha: float = Field(default=DEFAULT_ALPHA, gt=0, lt=1)
    method: CiMethod = EXACT


class PlanRequest(LotRequest):
    p_a: float = Probability
    p_r: float = Probability
    alpha: float = Field(default=DEFAULT_ALPHA, gt=0, lt=1)
    beta: float = Field(default=DEFAULT_BETA, gt=0, lt=1)


class SingleRequest(PlanRequest):
    limit: int = Field(default=DEFAULT_SEARCH_LIMIT, gt=0, le=MAX_SEARCH_LIMIT)


class DoubleRequest(PlanRequest):
    ratio: int = Field(default=1, gt=0, le=MAX_DOUBLE_RATIO)
    p: Optional[float] = Field(default=None, gt=0, lt=1)
    limit: int = Field(default=DEFAULT_SEARCH_LIMIT, gt=0, le=MAX_SEARCH_LIMIT)


class SequentialRequest(PlanRequest):
    p: Optional[float] = Field(default=None, gt=0, lt=1)
    defects: Optional[int] = Field(default=None, ge=0)
    cutoff: Optional[int] = Field(default=None, gt=0, le=MAX_SEQUENTIAL_CUTOFF)
    include_limits: bool = False

    @model_validator(mode="after")
    def check_sequential_lot_size(self):
        if self.distribution == "hypergeometric" and self.lot_size is not None:
            if self.lot_size > MAX_SEQUENTIAL_LOT_SIZE:
                raise ValueError(
                    f"lot_size must be at most {MAX_SEQUENTIAL_LOT_SIZE} for sequential hypergeometric calculations"
                )
        return self
