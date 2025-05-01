import pytest
from django.urls import reverse

from tests.utils import build_jwt_token


class TestBaseProxyView:
    """Prove that the generic view offers the login check logic.
    This is tested through the concrete implementations though.
    """

    @pytest.mark.parametrize(
        "url",
        [
            "/bevragingen/v1/personen",
            "/bevragingen/v1/bewoningen",
            "/bevragingen/v1/verblijfplaatshistorie",
        ],
    )
    def test_no_login(self, api_client, url):
        """Prove that accessing the view fails without a login token."""
        response = api_client.post(url)
        assert response.status_code == 401
        assert response.data == {
            "type": "https://datatracker.ietf.org/doc/html/rfc7235#section-3.1",
            "code": "notAuthenticated",
            "title": "Authentication credentials were not provided.",
            "detail": "",
            "status": 401,
            "instance": url,
        }

    def test_invalid_api_key(self, api_client, requests_mock, caplog, common_headers):
        """Prove that incorrect API-key settings are handled gracefully."""
        requests_mock.post(
            "/lap/api/brp",
            json={
                "type": "https://datatracker.ietf.org/doc/html/rfc7235#section-3.1",
                "title": "Niet correct geauthenticeerd.",
                "status": 401,
                "instance": "/lap/api/brp",
                "code": "authentication",
            },
            status_code=401,
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-personen")
        token = build_jwt_token(
            [
                "benk-brp-personen-api",
                "benk-brp-zoekvraag-postcode-huisnummer",
                "benk-brp-gegevensset-1",
            ]
        )
        response = api_client.post(
            url,
            {
                "type": "ZoekMetPostcodeEnHuisnummer",
                "postcode": "1074VE",
                "huisnummer": 1,
                "fields": ["naam.aanduidingNaamgebruik"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 502
        assert any(
            m.startswith("Access granted for 'personen.ZoekMetPostcodeEnHuisnummer' to '")
            for m in caplog.messages
        ), caplog.messages
        assert response.json() == {
            "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.6.3",
            "title": "Connection failed (bad gateway)",
            "status": 502,
            "detail": "Backend is improperly configured, final endpoint rejected our credentials.",
            "code": "backendConfig",
            "instance": "/bevragingen/v1/personen",
        }

    @pytest.mark.parametrize("remove_header", ["X-Correlation-ID", "X-User", "X-Task-Description"])
    def test_missing_common_headers(self, api_client, common_headers, remove_header):
        """Prove that not providing the common headers is accurately reported back"""
        url = reverse("brp-personen")
        token = build_jwt_token(
            ["benk-brp-personen-api", "benk-brp-zoekvraag-bsn", "benk-brp-gegevensset-1"]
        )
        headers = {
            "Authorization": f"Bearer {token}",
            **common_headers,
        }
        del headers[remove_header]
        response = api_client.post(
            url,
            {"type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": "000009830"},
            headers=headers,
        )
        assert response.status_code == 403
        assert response.json() == {
            "code": "missingHeaders",
            "detail": (
                "The following headers are required: X-User, X-Correlation-ID, X-Task-Description."
            ),
            "instance": "/bevragingen/v1/personen",
            "status": 403,
            "title": "You do not have permission to perform this action.",
            "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.3",
        }

    def test_error_response(self, api_client, requests_mock, caplog, common_headers):
        """Prove that Haal Centraal errors are handled gracefully."""
        requests_mock.post(
            "/lap/api/brp",
            json={
                "invalidParams": [
                    {
                        "name": "burgerservicenummer",
                        "code": "array",
                        "reason": "Parameter is geen array.",
                    }
                ],
                "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1",
                "title": "Een of meerdere parameters zijn niet correct.",
                "status": 400,
                "detail": "De foutieve parameter(s) zijn: burgerservicenummer.",
                "instance": "/lap/api/brp",
                "code": "paramsValidation",
            },
            status_code=400,
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-personen")
        token = build_jwt_token(
            ["benk-brp-personen-api", "benk-brp-zoekvraag-bsn", "benk-brp-gegevensset-1"]
        )
        response = api_client.post(
            url,
            {"type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": "000009830"},
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 400
        assert any(
            m.startswith("Access granted for 'personen.RaadpleegMetBurgerservicenummer' to '")
            for m in caplog.messages
        ), caplog.messages
        assert response.json() == {
            "code": "paramsValidation",
            "detail": "De foutieve parameter(s) zijn: burgerservicenummer.",
            "instance": "/bevragingen/v1/personen",
            "invalidParams": [
                {
                    "code": "array",
                    "name": "burgerservicenummer",
                    "reason": "Parameter is geen array.",
                }
            ],
            "status": 400,
            "title": "Een of meerdere parameters zijn niet correct.",
            "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1",
        }
