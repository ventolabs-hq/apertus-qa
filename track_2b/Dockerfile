# Apertus QA — runtime image. Python stdlib only: no pip install, so building needs nothing but the base image,
# and the running container needs no network except (optionally) the model endpoint.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
RUN useradd --system --uid 10001 --home /app app
WORKDIR /app
COPY data/snapshot/ /app/data/snapshot/
COPY src/ /app/src/
RUN mkdir -p /app/src/apertus_qa/replay && python -m compileall -q /app/src && \
    chown -R app /app/src/apertus_qa/stub /app/src/apertus_qa/replay
USER app
WORKDIR /app/src
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/health')" || exit 1
CMD ["python", "-m", "apertus_qa", "serve", "--port", "8080"]
