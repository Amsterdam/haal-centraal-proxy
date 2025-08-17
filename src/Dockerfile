FROM python:3.13-slim-bullseye AS builder
MAINTAINER datapunt@amsterdam.nl

RUN apt update && apt install --no-install-recommends -y \
    build-essential \
    libpq-dev
COPY requirements* ./
ARG PIP_REQUIREMENTS=requirements.txt
RUN python -m pip install uwsgi
# The `--no-deps` has been added because of a pip bug with --require-hashes
# The dependencies have already been resolved during the generation of
# the requirements.txt, so adding `--no-deps` can safely be done.
RUN python -m pip install --no-cache-dir --no-deps -r $PIP_REQUIREMENTS

# Start runtime image,
FROM python:3.13-slim-bullseye
RUN useradd -U -r haalcentraalapi
RUN apt update && apt install --no-install-recommends -y \
    curl \
    netcat-openbsd

# Copy python build artifacts from builder image
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

WORKDIR /app
COPY . ./
COPY config/ca/* /usr/local/share/ca-certificates/

# Have some defaults so the container is easier to start
ENV DJANGO_SETTINGS_MODULE=haal_centraal_proxy.settings \
    DJANGO_DEBUG=false \
    UWSGI_HTTP_SOCKET=:8000 \
    UWSGI_MODULE=haal_centraal_proxy.wsgi \
    UWSGI_CALLABLE=application \
    UWSGI_MASTER=1 \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
RUN pip install --no-cache-dir setuptools  # workaround for missing pkg_resources in opentelemetry

RUN python manage.py collectstatic --noinput \
 && update-ca-certificates --verbose

EXPOSE 8000
USER haalcentraalapi
CMD ["uwsgi"]
