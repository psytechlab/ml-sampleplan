import os

from sampleplan.service import DEFAULT_LIMIT


def _positive_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, default))
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error

    if value <= 0:
        raise ValueError(f"{name} must be larger than 0")

    return value


MAX_LOT_SIZE = _positive_env("SAMPLEPLAN_MAX_LOT_SIZE", 1_000_000)
MAX_SEQUENTIAL_LOT_SIZE = min(MAX_LOT_SIZE, 20_000)
MAX_SEARCH_LIMIT = _positive_env("SAMPLEPLAN_MAX_SEARCH_LIMIT", 100_000)
MAX_DOUBLE_RATIO = _positive_env("SAMPLEPLAN_MAX_DOUBLE_RATIO", 100)
MAX_SEQUENTIAL_CUTOFF = _positive_env("SAMPLEPLAN_MAX_SEQUENTIAL_CUTOFF", 2_000)
DEFAULT_SEARCH_LIMIT = min(DEFAULT_LIMIT, MAX_SEARCH_LIMIT)
