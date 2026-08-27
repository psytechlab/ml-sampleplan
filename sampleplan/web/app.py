from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from sampleplan.service import (
    SamplePlanError,
    compute_ci,
    compute_double,
    compute_sequential,
    compute_single,
)
from sampleplan.web.config import MAX_SEQUENTIAL_CUTOFF
from sampleplan.web.forms import form_descriptions
from sampleplan.web.models import (
    CiRequest,
    DoubleRequest,
    SequentialRequest,
    SingleRequest,
)

STATIC_DIR = Path(__file__).parent / "static"


def _version() -> str:
    try:
        return version("sampleplan")
    except PackageNotFoundError:
        return "unknown"


def create_app() -> FastAPI:
    app = FastAPI(
        title="sampleplan API",
        description=(
            "Sample-size calculations for confidence intervals and acceptance sampling. "
            "See the accompanying paper: https://arxiv.org/abs/2405.11919"
        ),
        version=_version(),
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.exception_handler(SamplePlanError)
    async def sampleplan_error_handler(_request: Request, exc: SamplePlanError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "version": _version()}

    @app.get("/api/forms")
    async def forms():
        return form_descriptions()

    @app.post("/api/ci")
    async def ci(request: CiRequest):
        return await run_in_threadpool(compute_ci, **request.model_dump())

    @app.post("/api/single")
    async def single(request: SingleRequest):
        return await run_in_threadpool(compute_single, **request.model_dump())

    @app.post("/api/double")
    async def double(request: DoubleRequest):
        return await run_in_threadpool(compute_double, **request.model_dump())

    @app.post("/api/sequential")
    async def sequential(request: SequentialRequest):
        return await run_in_threadpool(
            compute_sequential,
            **request.model_dump(),
            max_cutoff=MAX_SEQUENTIAL_CUTOFF,
        )

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
