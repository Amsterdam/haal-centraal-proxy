from django.urls import reverse

from tests.utils import build_jwt_token


class TestBrpBewoningenView:
    """Prove that the API works as advertised."""

    RESPONSE_BEWONINGEN = {
        "bewoningen": [
            {
                "adresseerbaarObjectIdentificatie": "0518010000832200",
                "periode": {"datumVan": "2020-09-24", "datumTot": "2020-09-25"},
                "bewoners": [{"burgerservicenummer": "999993240"}],
                "mogelijkeBewoners": [],
            }
        ]
    }

    def test_address_id_search(self, api_client, requests_mock, common_headers):
        """Prove that search is possible"""
        requests_mock.post(
            "/lap/api/brp/bewoning",
            json=self.RESPONSE_BEWONINGEN,
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-bewoningen")
        token = build_jwt_token(["benk-brp-bewoning-api"])
        response = api_client.post(
            url,
            {
                "type": "BewoningMetPeildatum",
                "adresseerbaarObjectIdentificatie": "0518010000832200",
                "peildatum": "2020-09-24",
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response
        assert response.json() == self.RESPONSE_BEWONINGEN, response.data

    def test_address_id_search_deny(self, api_client, common_headers):
        """Prove that access is checked"""
        url = reverse("brp-bewoningen")
        token = build_jwt_token(["benk-brp-SOME-OTHER-api"])
        response = api_client.post(
            url,
            {
                "type": "BewoningMetPeildatum",
                "adresseerbaarObjectIdentificatie": "0518010000832200",
                "peildatum": "2020-09-24",
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 403, response.data
        assert response.data["code"] == "permissionDenied"
        assert response.data == {
            "code": "permissionDenied",
            "detail": "Required scopes not given in token.",
            "instance": "/bevragingen/v1/bewoningen",
            "status": 403,
            "title": "You do not have permission to perform this action.",
            "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.3",
        }
