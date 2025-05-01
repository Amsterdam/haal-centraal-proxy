from django.urls import reverse

from tests.utils import build_jwt_token


class TestBrpVerblijfplaatshistorieView:
    """Prove that the API works as advertised."""

    RESPONSE_VERBLIJFPLAATS = {
        "verblijfplaatsen": [
            {
                "type": "Adres",
                "verblijfadres": {
                    "officieleStraatnaam": "Erasmusweg",
                    "korteStraatnaam": "Erasmusweg",
                    "huisnummer": 471,
                    "postcode": "2532CN",
                    "woonplaats": "'s-Gravenhage",
                },
                "functieAdres": {"code": "W", "omschrijving": "woonadres"},
                "adresseerbaarObjectIdentificatie": "0518010000832200",
                "nummeraanduidingIdentificatie": "0518200000832199",
                "gemeenteVanInschrijving": {"code": "0518", "omschrijving": "'s-Gravenhage"},
                "datumVan": {
                    "type": "Datum",
                    "datum": "1990-04-27",
                    "langFormaat": "27 april 1990",
                },
                "adressering": {
                    "adresregel1": "Erasmusweg 471",
                    "adresregel2": "2532 CN  'S-GRAVENHAGE",
                },
            }
        ]
    }

    def test_bsn_date_search(self, api_client, requests_mock, common_headers):
        """Prove that search is possible"""
        requests_mock.post(
            "/lap/api/brp/verblijfplaatshistorie",
            json=self.RESPONSE_VERBLIJFPLAATS,
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-verblijfplaatshistorie")
        token = build_jwt_token(["benk-brp-verblijfplaatshistorie-api"])
        response = api_client.post(
            url,
            {
                "type": "RaadpleegMetPeildatum",
                "burgerservicenummer": "999993240",
                "peildatum": "2020-09-24",
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response
        assert response.json() == self.RESPONSE_VERBLIJFPLAATS, response.data

    def test_bsn_date_search_deny(self, api_client, common_headers):
        """Prove that access is checked"""
        url = reverse("brp-verblijfplaatshistorie")
        token = build_jwt_token(["benk-brp-SOME-OTHER-api"])
        response = api_client.post(
            url,
            {
                "type": "RaadpleegMetPeildatum",
                "burgerservicenummer": "999993240",
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
            "instance": "/bevragingen/v1/verblijfplaatshistorie",
            "status": 403,
            "title": "You do not have permission to perform this action.",
            "type": "https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.3",
        }
