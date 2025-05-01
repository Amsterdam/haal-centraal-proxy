# Haal Centraal API

This is a proxy service to connect to the Haal Centraal API.
It filters requests and enforces token-based authorization.

# Reason

Haal Centraal offers national services for accessing government data.
These services are designed to support broad access, and don't offer much refined authorization policies.
Such feature has to be implemented by each municipality that implements the API.

This service does this based on policy files (tbd, but likely in "Amsterdam Schema").

# Installation

Requirements:

* Python >= 3.12
* Recommended: Docker/Docker Compose (or pyenv for local installs)

## Using Docker Compose

Run docker compose:
```shell
docker compose up
```

Navigate to `localhost:8095`.

## Using Local Python

Create a virtualenv:

```shell
python3 -m venv venv
source venv/bin/activate
```

Install all packages in it:
```shell
pip install -U wheel pip
cd src/
make install  # installs src/requirements_dev.txt
```

Start the Django application:
```shell
export PUB_JWKS="$(cat jwks_test.json)"
export HAAL_CENTRAAL_BRP_URL="http://localhost:5010/haalcentraal/api/brp/personen"
export DJANGO_DEBUG=true

./manage.py runserver localhost:8000
```

## Example Requests

Example request (directly to the Haal Centraal Mock API):

    curl -X POST http://localhost:5010/haalcentraal/api/brp/personen -H 'Content-Type: application/json' -d '{"type": "ZoekMetPostcodeEnHuisnummer", "postcode": "1074VE", "huisnummer": 1, "fields": ["naam"]}'

And the same can be repeated on the Django instance if you pass a token:

    export TOKEN="$(./get-token.py benk-brp-personen-api benk-brp-zoekvraag-postcode-huisnummer benk-brp-gegevensset-1)"
    curl -X POST http://localhost:8000/bevragingen/v1/personen -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -H "X-User: foo" -H "X-Task-Description: foo" -X "X-Correlation-ID: foo" -d '{"type": "ZoekMetPostcodeEnHuisnummer", "postcode": "1074VE", "huisnummer": 1}'

Same for search by BSN:

    export TOKEN="$(./get-token.py benk-brp-personen-api benk-brp-zoekvraag-bsn benk-brp-gegevensset-1)"
    curl -X POST http://localhost:8000/bevragingen/v1/personen -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" -H "X-User: foo" -H "X-Task-Description: foo" -X "X-Correlation-ID: foo" -d '{"type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": ["010082426"]}'

### Notes

The *type* field is required for all request types.
The *fields* parameter is not required in the proxy, as it will be generated based on your token scopes.

All possible parameters are documented in the [Haal Centraal documentation](https://brp-api.github.io/Haal-Centraal-BRP-bevragen/).


## Applied Request Transformations

For the *personen* endpoint, some parameters are automatically filled in based on the token permissions if these are missing in the original request.

* **fields** will be automatically filled in based on the permissions.
* **gemeenteVanInschrijving** will be limited to Amsterdam unless the user may search nationwide (for *type=ZoekMetPostcodeEnHuisnummer* or scope *benk-brp-zoekvraag-postcode-huisnummer-landelijk*).
* **inclusiefOverledenPersonen=true** will be included when the *benk-brp-inclusief-overledenen* scope is present and the *type* supports this parameter.

This behavior can be overwritten by providing the parameter in the original request.
Those parameters will be validated against the ruleset.
In practice, this means that using *inclusiefOverledenPersonen=false* would work,
but specifying *true* requires the token scope to be there.

## Applied Response Transformations

The *personen* endpoint will transform the responses:

By default, Haal Centraal [hides empty/null/false values](https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/features-overzicht#geennullfalse-waarde-leeg-object-waarde-en-standaard-waarde).
This can be overwritten by adding ``?resultaat-formaat=volledig`` to the URL,
so explicit `null` values or empty arrays are included.
As such, clients can detect whether a field was actually empty, or omitted due to permissions.
Note this does not apply to the  [automatically included fields](https://brp-api.github.io/Haal-Centraal-BRP-bevragen/v2/features-overzicht#standaard-geleverde-velden).

When the scope *benk-brp-inclusief-geheim* is missing, persons with *geheimhoudingPersoonsgegevens=1* will be omitted from the response.
That flags indicates that data may not be shared with organisations such as churches, sports clubs and charities.

In case more permisions are missing from the expected response, or a BSN search returns no results,
most likely the scope *benk-brp-landelijk* or *benk-brp-zoekvraag-postcode-huisnummer-landelijk* is missing.
This will limit the search to persons within Amsterdam only.

## Encryption/decryption of burgerservicenummers

For users with the scope *benk-brp-encrypt-bsn* all burgerservicenummers in the response will be
encrypted. Subsequent calls to the API can be made with the encrypted burgerservicenummers and will
be decrypted when the scope is present. The audit logs will still contain the original value.

When unecrypted burgerservicenummers are in requests with the scope present, a permission denied
response will be returned.

## Available Endpoints

The following URLs are available:

| API                                      | Description                              | Setting for Proxy URL            | Docs                                                                      |
|------------------------------------------|------------------------------------------|----------------------------------|---------------------------------------------------------------------------|
| `/bevragingen/v1/personen`               | Person details.                          | `BRP_PERSONEN_URL`               | [docs](https://brp-api.github.io/Haal-Centraal-BRP-bevragen/)             |
| `/bevragingen/v1/bewoningen`             | Who lived at an address.                 | `BRP_BEWONINGEN_URL`             | [docs](https://brp-api.github.io/Haal-Centraal-BRP-bewoning/)             |
| `/bevragingen/v1/verblijfplaatshistorie` | All addresses where someone lived.       | `BRP_VERBLIJFPLAATSHISTORIE_URL` | [docs](https://brp-api.github.io/Haal-Centraal-BRP-historie-bevragen/)    |

## Environment Settings

The following environment variables are useful for configuring a local development environment:

* `DJANGO_DEBUG` to enable debugging (true/false).
* `LOG_LEVEL` log level for application code (default is `DEBUG` for debug, `INFO` otherwise).
* `AUDIT_LOG_LEVEL` log level for audit messages (default is `INFO`).
* `DJANGO_LOG_LEVEL` log level for Django internals (default is `INFO`).
* `PUB_JWKS` allows to give publically readable JSON Web Key Sets in JSON format (good default: `jq -c < src/jwks_test.json`).

### Connections

* `BRP_OAUTH_TOKEN_URL` should be the endpoint for requesting OAuth tokens.
* `BRP_URL` base endpoint for the BRP API's. This also works as default for the endpoints:
  * `BRP_PERSONEN_URL` endpoint for the Haal Centraal BRP Personen API.
  * `BRP_BEWONINGEN_URL` endpoint for the BRP occupancy URL.
  * `VERBLIJFPLAATSHISTORIE_URL` endpoint for the address history URL.
* `BRP_MTLS_CERT_FILE` the mTLS client certificate.
* `BRP_MTLS_KEY_FILE` the mTLS client key file.

The values for these can be found in the [Aansluitinstructies via Diginetwerk voor de stelselapplicaties](https://www.rvig.nl/Aansluitinstructies-Diginetwerk-voor-stelselapplicaties).

### Deployment

* `ALLOWED_HOSTS` will limit which domain names can connect.
* `AZURE_APPI_CONNECTION_STRING` Azure Insights configuration.
* `AZURE_APPI_AUDIT_CONNECTION_STRING` Same, for a special audit logging.
* `CLOUD_ENV=azure` will enable Azure-specific telemetry.
* `CACHE_URL` allows to define a cache for OAuth tokens (default is using local momory).
* `STATIC_URL` defines the base URL for static files (e.g. to point to a CDN).
* `OAUTH_JWKS_URL` point to a public JSON Web Key Set, e.g. `https://login.microsoftonline.com/{tenant_uuid or 'common'}/discovery/v2.0/keys`.
* `OAUTH_CHECK_CLAIMS` should be `aud=AUDIENCE-IN-TOKEN,iss=ISSUER-IN-TOKEN`.

### Hardening deployment

* `SESSION_COOKIE_SECURE` is already true in production.
* `CSRF_COOKIE_SECURE` is already true in production.
* `SECRET_KEY` is used for various encryption code.
* `CORS_ALLOW_ALL_ORIGINS` can be true/false to allow all websites to connect.
* `CORS_ALLOW_HEADERS` allows additional headers in the request.
* `CORS_ALLOWED_ORIGINS` allows a list of origin URLs to use.
* `CORS_ALLOWED_ORIGIN_REGEXES` supports a list of regex patterns fow allowed origins.
* `HAAL_CENTRAAL_BRP_ENCRYPTION_SALTS` a list of salts used to encrypt data. The first item will be used to encrypt
   new values, the other values can be used for rotation.

# Developer Notes

Run `make` in the `src` folder to have a help-overview of all common developer tasks.

## Package Management

The packages are managed with *pip-compile*.

To add a package, update the `requirements.in` file and run `make requirements`.
This will update the "lockfile" aka `requirements.txt` that's used for pip installs.

To upgrade all packages, run `make upgrade`, followed by `make install` and `make test`.
Or at once if you feel lucky: `make upgrade install test`.

## Environment Settings

Consider using *direnv* for automatic activation of environment variables.
It automatically sources an ``.envrc`` file when you enter the directory.
This file should contain all lines in the `export VAR=value` format.

In a similar way, *pyenv* helps to install the exact Python version,
and will automatically activate the virtualenv when a `.python-version` file is found:

```shell
pyenv install 3.12.4
pyenv virtualenv 3.12.4 haal-centraal-proxy
echo haal-centraal-proxy > .python-version
```

## Test BSN Numbers

The docker mock API uses this [JSON test dataset](https://github.com/BRP-API/Haal-Centraal-BRP-bevragen/blob/master/src/config/BrpService/test-data.json).
We've found these to be useful:

| Feature                    | BSN       |
|----------------------------|-----------|
| Met adelijke titel         | 000009830 |
| Met parter                 | 010082426 |
| Gescheiden                 | 999991905 |
| Overleden                  | 999970239 |
| Staatloos                  | 999991504 |
| Verblijfstitel             | 000009908 |
| Immigratie                 | 000009842 |
| heeft ouders met bsn       | 999970665 |
| Gezag double combo         | 999970057 |
| Met einddatum en gezag     | 999970884 |
| Indicatiecurateel register | 999993690 |
| Geëmigreerd                | 999990585 |
| inOnderzoek                | 999990378 |
| Nationaliteit onbekend     | 999993367 |

The acceptance environment (proefomgeving) of Haal Centraal uses a different [GABA-V test dataset](https://www.rvig.nl/media/288)
to simulate the production environment in the best possible way.

Also note that this proxy can limit the results.

* When the scope *benk-brp-landelijk* is missing, only results within Amsterdam are returned.
* When the scope *benk-brp-geheimhouding-persoonsgegevens* is missing, persons with *geheimhoudingPersoonsgegevens* are omitted.
