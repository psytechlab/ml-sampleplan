import os

import uvicorn


def main():
    uvicorn.run(
        "sampleplan.web.app:app",
        host=os.getenv("SAMPLEPLAN_HOST", "0.0.0.0"),
        port=int(os.getenv("SAMPLEPLAN_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
