FROM python:3.12-slim AS builder

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir "poetry==2.2.1" "poetry-plugin-export==1.10.0" \
    && poetry export --only main --extras web --format requirements.txt --output /tmp/requirements.txt \
    && /usr/local/bin/python -m venv "$VIRTUAL_ENV" \
    && "$VIRTUAL_ENV/bin/pip" install --no-cache-dir --no-deps --requirement /tmp/requirements.txt

COPY pyproject.toml README.md ./
COPY sampleplan ./sampleplan
RUN "$VIRTUAL_ENV/bin/pip" install --no-cache-dir --no-deps .


FROM python:3.12-slim AS runtime

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=builder /opt/venv /opt/venv

USER app
WORKDIR /app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"

CMD ["uvicorn", "sampleplan.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
