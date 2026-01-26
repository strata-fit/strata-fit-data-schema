FROM harbor2.vantage6.ai/infrastructure/algorithm-base:4.13
  
WORKDIR /app
ARG PKG_NAME="strata_fit_v6_data_validator_py"

ENV PKG_NAME=${PKG_NAME}

COPY . /app
RUN pip install /app 

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Dispatcher entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
# no CMD – Vantage6 passes what it needs as env-vars; our entrypoint decides