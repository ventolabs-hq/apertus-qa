# Report builder only (NOT the app image). Renders technical_report.md -> VentoLabs_Report.pdf with pandoc + WeasyPrint.
# Debian packages only, $0, no TeX. Used by `make report`.
FROM debian:trixie-slim
RUN for i in 1 2 3 4 5; do apt-get -o Acquire::Retries=5 update && break; sleep 5; done \
 && DEBIAN_FRONTEND=noninteractive apt-get -o Acquire::Retries=5 install -y --no-install-recommends pandoc weasyprint fonts-dejavu-core fonts-liberation2 poppler-utils \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /work
