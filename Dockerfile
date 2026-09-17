FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PKG_NAME=strata_fit_v6_data_validator_py

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir /app

# Dispatcher entrypoint: RUN_MODE selects cli / api / algorithm (fixed exec
# targets only, no shell-evaluated input — see entrypoint.sh).
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
# no CMD – RUN_MODE (and API_HOST/API_PORT for api mode) decide via env vars
