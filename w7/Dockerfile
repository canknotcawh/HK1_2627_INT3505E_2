FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir .

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN groupadd --system app && useradd --system --gid app app
COPY --from=builder /opt/venv /opt/venv
COPY src ./src
COPY wsgi.py gunicorn.conf.py docker-entrypoint.sh ./
RUN chmod 0555 docker-entrypoint.sh && chown -R app:app /app
USER app
EXPOSE 5000
ENTRYPOINT ["./docker-entrypoint.sh"]
