# Description: Builds every Acme service image from one definition, selected by the SERVICE build arg.
# Created by: Mustafa Can Caliskan
# Date: 2026-08-01

FROM python:3.12-slim

WORKDIR /app

COPY services/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# The Weaver-generated package is a build input like any other source file.
COPY generated/python/acme_semconv ./acme_semconv
COPY services/common ./common

ARG SERVICE
COPY services/${SERVICE} ./service

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

CMD ["python", "service/main.py"]
