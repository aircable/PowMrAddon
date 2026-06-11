ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.22
FROM ${BUILD_FROM}

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt

RUN apk add --no-cache python3 py3-pip \
    && python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

COPY run.sh /app/run.sh
COPY app /app/app

RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]
