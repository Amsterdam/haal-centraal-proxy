from copy import deepcopy

import pytest
from django.urls import reverse
from haal_centraal_proxy.bevragingen.fields import read_dataset_fields_files
from haal_centraal_proxy.bevragingen.permissions import ParameterPolicy
from haal_centraal_proxy.bevragingen.views.base import SCOPE_ENCRYPT_BSN
from haal_centraal_proxy.bevragingen.views.personen import (
    SCOPE_ALLOW_CONFIDENTIAL_PERSONS,
    SCOPE_INCLUDE_DECEASED,
    SCOPE_NATIONWIDE,
    BrpPersonenView,
    _group_dotted_names,
)

from tests.utils import build_jwt_token


@pytest.fixture
def gegevensset_1():
    return sorted(
        read_dataset_fields_files("dataset_fields/personen/benk-brp-gegevensset-1.txt").keys()
    )


class TestBrpPersonenView:
    """Prove that the BRP view works as advertised.

    This incluedes tests that are specific for the BRP (not generic tests).
    """

    RESPONSE_POSTCODE_HUISNUMMER = {
        "type": "ZoekMetPostcodeEnHuisnummer",
        "personen": [
            {
                "naam": {
                    "voornamen": "Ronald Franciscus Maria",
                    "geslachtsnaam": "Moes",
                    "voorletters": "R.F.M.",
                    "volledigeNaam": "Ronald Franciscus Maria Moes",
                    "aanduidingNaamgebruik": {
                        "code": "E",
                        "omschrijving": "eigen geslachtsnaam",
                    },
                }
            }
        ],
    }

    RESPONSE_BSN = {
        **RESPONSE_POSTCODE_HUISNUMMER,
        "type": "RaadpleegMetBurgerservicenummer",
    }

    RESPONSE_ENCRYPT_BSN = deepcopy(RESPONSE_POSTCODE_HUISNUMMER)
    RESPONSE_ENCRYPT_BSN["personen"][0]["burgerservicenummer"] = "999993367"

    def test_postcode_search(self, api_client, requests_mock, common_headers):
        """Prove that search is possible"""
        requests_mock.post(
            "/lap/api/brp",
            json=self.RESPONSE_POSTCODE_HUISNUMMER,
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
                "fields": ["naam.aanduidingNaamgebruik"],  # no-op for mocked response.
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response.data
        assert response.json() == self.RESPONSE_POSTCODE_HUISNUMMER, response.data

    def test_postcode_search_deny(self, api_client, common_headers):
        """Prove that search is possible"""
        url = reverse("brp-personen")
        token = build_jwt_token(["benk-brp-personen-api"])

        response = api_client.post(
            url,
            {
                "type": "ZoekMetPostcodeEnHuisnummer",
                "postcode": "1074VE",
                "huisnummer": 1,
                "fields": ["naam"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 403, response.data
        assert response.data["code"] == "permissionDenied"

    def test_transform_include_nulls_zipcode(self, api_client, requests_mock, common_headers):
        """Prove that search is possible"""
        requests_mock.post(
            "/lap/api/brp",
            json=self.RESPONSE_POSTCODE_HUISNUMMER,
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
            f"{url}?resultaat-formaat=volledig",
            {
                "type": "ZoekMetPostcodeEnHuisnummer",
                "postcode": "1074VE",
                "huisnummer": 1,
                # No fields, is auto filled with all options of gegevensset-1.
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response.data
        assert response.json() == {
            "type": "ZoekMetPostcodeEnHuisnummer",
            "personen": [
                {
                    "naam": {
                        "aanduidingNaamgebruik": {
                            "code": "E",
                            "omschrijving": "eigen geslachtsnaam",
                        },
                        "geslachtsnaam": "Moes",
                        "volledigeNaam": "Ronald Franciscus Maria Moes",
                        "voorletters": "R.F.M.",
                        "voornamen": "Ronald Franciscus Maria",
                        "voorvoegsel": None,  # included this missing field
                        "adellijkeTitelPredicaat": None,
                    },
                    "adressering": {  # included this missing object
                        "adresregel1": None,  # included this missing field
                        "adresregel2": None,  # included this missing field
                        "adresregel3": None,  # included this missing field
                        "land": None,  # included this missing field
                    },
                    "burgerservicenummer": None,  # included this missing field
                    "geboorte": {  # included this missing object
                        "datum": None,  # included this missing field
                    },
                    "leeftijd": None,  # included this missing field
                    "geslacht": None,  # empty object
                }
            ],
        }

    def test_transform_include_nulls_bsn(self, api_client, requests_mock, common_headers):
        """Prove that search is possible"""
        requests_mock.post(
            "/lap/api/brp",
            json=self.RESPONSE_BSN,
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-personen")
        token = build_jwt_token(
            [
                "benk-brp-personen-api",
                "benk-brp-zoekvraag-bsn",
                "benk-brp-gegevensset-9",
            ]
        )
        response = api_client.post(
            f"{url}?resultaat-formaat=volledig",
            {
                "type": "RaadpleegMetBurgerservicenummer",
                "burgerservicenummer": [""],
                # No fields, is auto filled with all options of gegevensset-1.
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response.data
        assert response.json() == {
            "type": "RaadpleegMetBurgerservicenummer",
            "personen": [
                {
                    "naam": {
                        "aanduidingNaamgebruik": {
                            "code": "E",
                            "omschrijving": "eigen geslachtsnaam",
                        },
                        "geslachtsnaam": "Moes",
                        "volledigeNaam": "Ronald Franciscus Maria Moes",
                        "voorletters": "R.F.M.",
                        "voornamen": "Ronald Franciscus Maria",
                        "voorvoegsel": None,  # included this missing field
                        "adellijkeTitelPredicaat": None,  # included this
                    },
                    "adressering": {  # included this missing object
                        "aanhef": None,  # included this missing field
                        "aanschrijfwijze": {  # included this missing object
                            "aanspreekvorm": None,  # included this missing field
                            "naam": None,  # included this missing field
                        },
                        "adresregel1": None,  # included this missing field
                        "adresregel2": None,  # included this missing field
                        "adresregel3": None,  # included this missing field
                        "gebruikInLopendeTekst": None,  # included this missing field
                        "land": None,  # included this missing field
                    },
                    "datumInschrijvingInGemeente": None,
                    "geboorte": {  # included this missing object
                        "datum": None,  # included this missing field
                    },
                    "immigratie": {  # included this missing object
                        "datumVestigingInNederland": None,  # included this missing field
                    },
                    "indicatieCurateleRegister": None,
                    "kinderen": [],  #  included empty array
                    "nationaliteiten": [],  # included empty array
                    "burgerservicenummer": None,  # included this missing field
                    "leeftijd": None,  # included this missing field
                    "aNummer": None,
                    "gemeenteVanInschrijving": None,  # empty object
                    "geslacht": None,  # empty object (not expanded)
                    "gezag": [],  # included empty array
                    "ouders": [],  # included this missing object
                    "overlijden": {  # included this missing object
                        "datum": None,  # included this missing field
                    },
                    "partners": [],  # included empty array
                    "verblijfplaats": {  # included this missing object
                        "adresseerbaarObjectIdentificatie": None,  # included this missing field
                        "datumVan": None,  # included this missing field
                        "functieAdres": None,  # included this missing field
                        "nummeraanduidingIdentificatie": None,  # included this missing field
                        "verblijfadres": {  # included this missing object
                            "aanduidingBijHuisnummer": None,  # included this missing field
                            "huisletter": None,  # included this missing field
                            "huisnummer": None,  # included this missing field
                            "huisnummertoevoeging": None,  # included this missing field
                            "korteStraatnaam": None,  # included this missing field
                            "land": None,  # included this missing field
                            "locatiebeschrijving": None,  # included this missing field
                            "officieleStraatnaam": None,  # included this missing field
                            "postcode": None,  # included this missing field
                            "regel1": None,  # included this missing field
                            "regel2": None,  # included this missing field
                            "regel3": None,  # included this missing field
                            "woonplaats": None,  # included this missing field
                        },
                    },
                    "verblijfstitel": {  # included this missing object
                        "aanduiding": None,  # included this missing field
                        "datumEinde": None,  # included this missing field
                        "datumIngang": None,  # included this missing field
                    },
                }
            ],
        }

    def test_transform_allow_nationwide(self):
        """Prove that 'gemeenteVanInschrijving' won't be added if there is nationwide access."""
        view = BrpPersonenView()
        view.user_scopes = {
            "benk-brp-zoekvraag-bsn",
            "benk-brp-gegevensset-1",
            SCOPE_NATIONWIDE,
        }
        hc_request = {
            "type": "RaadpleegMetBurgerservicenummer",
            "fields": ["naam.aanduidingNaamgebruik"],
        }
        view.transform_request(hc_request)
        assert view.inserted_id_fields == ["aNummer", "burgerservicenummer"]

        assert hc_request == {
            "type": "RaadpleegMetBurgerservicenummer",
            # Note that the 'fields' are also updated for logging purposes
            "fields": ["naam.aanduidingNaamgebruik", "aNummer", "burgerservicenummer"],
            # no gemeenteVanInschrijving added.
        }

    def test_transform_enforce_municipality(self):
        """Prove that 'gemeenteVanInschrijving' will be added."""
        view = BrpPersonenView()
        view.user_scopes = {"benk-brp-zoekvraag-bsn", "benk-brp-gegevensset-1"}
        hc_request = {
            "type": "RaadpleegMetBurgerservicenummer",
            "fields": ["naam.aanduidingNaamgebruik"],
        }
        view.transform_request(hc_request)
        assert view.inserted_id_fields == ["aNummer", "burgerservicenummer"]

        assert hc_request == {
            "type": "RaadpleegMetBurgerservicenummer",
            # Note that the 'fields' are also updated for logging purposes
            "fields": ["naam.aanduidingNaamgebruik", "aNummer", "burgerservicenummer"],  # added
            "gemeenteVanInschrijving": "0363",  # added (missing scope to seek outside area)
        }

    def test_transform_do_not_allow_deceased_for_bsn_search(self):
        """Prove that 'inclusiefOverledenPersonen' is not automatically added for the scope.
        When searched on BSN.
        """
        view = BrpPersonenView()
        view.user_scopes = {
            "benk-brp-zoekvraag-bsn",
            "benk-brp-gegevensset-1",
            SCOPE_NATIONWIDE,
            SCOPE_INCLUDE_DECEASED,
        }
        hc_request = {
            "type": "RaadpleegMetBurgerservicenummer",
            "fields": ["naam.aanduidingNaamgebruik"],
        }
        view.transform_request(hc_request)
        assert view.inserted_id_fields == ["aNummer", "burgerservicenummer"]

        assert hc_request == {
            "type": "RaadpleegMetBurgerservicenummer",
            "fields": ["naam.aanduidingNaamgebruik", "aNummer", "burgerservicenummer"],
        }

    def test_transform_allow_deceased(self):
        """Prove that 'inclusiefOverledenPersonen' is automatically added for the scope."""
        view = BrpPersonenView()
        view.user_scopes = {
            "benk-brp-zoekvraag-bsn",
            "benk-brp-gegevensset-1",
            SCOPE_NATIONWIDE,
            SCOPE_INCLUDE_DECEASED,
        }
        hc_request = {
            "type": "ZoekMetPostcodeEnHuisnummer",
            "fields": ["naam.aanduidingNaamgebruik"],
        }
        view.transform_request(hc_request)
        assert view.inserted_id_fields == ["burgerservicenummer"]

        assert hc_request == {
            "type": "ZoekMetPostcodeEnHuisnummer",
            "fields": ["naam.aanduidingNaamgebruik", "burgerservicenummer"],
            "inclusiefOverledenPersonen": True,
        }

    def test_transform_add_fields(self, gegevensset_1):
        """Prove that 'fields' and 'gemeente-filter is added."""
        view = BrpPersonenView()
        view.user_scopes = {"benk-brp-zoekvraag-bsn", "benk-brp-gegevensset-1"}
        hc_request = {
            "type": "RaadpleegMetBurgerservicenummer",
        }

        view.transform_request(hc_request)
        hc_request["fields"].sort()

        assert hc_request == {
            "type": "RaadpleegMetBurgerservicenummer",
            "gemeenteVanInschrijving": "0363",  # added (missing scope to seek outside area)
            "fields": gegevensset_1,  # added (default all allowed fields)
        }

    def test_transform_add_fields_limited(self):
        """Prove that 'fields' and 'gemeente-filter is added."""
        view = BrpPersonenView()
        view.user_scopes = {"benk-brp-zoekvraag-postcode-huisnummer", "benk-brp-gegevensset-1"}
        hc_request = {
            "type": "ZoekMetPostcodeEnHuisnummer",
        }

        view.transform_request(hc_request)
        hc_request["fields"].sort()

        assert hc_request == {
            "type": "ZoekMetPostcodeEnHuisnummer",
            "gemeenteVanInschrijving": "0363",  # added (missing scope to seek outside area)
            "fields": [
                # added (very limited set due to constraints of both the fields CSV and scope)
                "adressering.adresregel1",
                "adressering.adresregel2",
                "adressering.adresregel3",
                "adressering.land",
                "burgerservicenummer",
                "geboorte.datum",
                "geslacht",
                "leeftijd",
                "naam.adellijkeTitelPredicaat",
                "naam.geslachtsnaam",
                "naam.volledigeNaam",
                "naam.voorletters",
                "naam.voornamen",
                "naam.voorvoegsel",
                # not: adresseringBinnenland.adresregel1
                # not: adresseringBinnenland.adresregel2
            ],
        }

    def test_transform_missing_sets(self, api_client, common_headers):
        """Prove that not having access to a set is handled gracefully."""
        url = reverse("brp-personen")
        token = build_jwt_token(
            ["benk-brp-personen-api", "benk-brp-zoekvraag-bsn", "benk-brp-gegevensset-foobar"]
        )

        response = api_client.post(
            url,
            {"type": "RaadpleegMetBurgerservicenummer"},
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 403, response.data
        assert response.data["code"] == "permissionDenied"
        assert response.data["detail"] == (
            "U bent niet geautoriseerd voor een gegevensset bij deze operatie."
        )

    @pytest.mark.parametrize("hide", [True, False])
    def test_transform_hide_confidential(
        self, api_client, requests_mock, hide, caplog, common_headers
    ):
        """Prove that confidential persons are hidden."""
        person1 = {
            "naam": {"geslachtsnaam": "FOO"},
        }
        person2 = {
            "naam": {"geslachtsnaam": "BAR"},
            "geheimhoudingPersoonsgegevens": "1",
        }
        requests_mock.post(
            "/lap/api/brp",
            json={
                "type": "ZoekMetPostcodeEnHuisnummer",
                "personen": [person1, person2],
            },
            headers={"content-type": "application/json"},
        )
        url = reverse("brp-personen")
        scopes = [
            "benk-brp-personen-api",
            "benk-brp-zoekvraag-postcode-huisnummer",
            "benk-brp-gegevensset-1",
        ]
        if not hide:
            scopes.append(SCOPE_ALLOW_CONFIDENTIAL_PERSONS)
        response = api_client.post(
            url,
            {
                "type": "ZoekMetPostcodeEnHuisnummer",
                "postcode": "1074VE",
                "huisnummer": 1,
                "fields": ["naam.geslachtsnaam"],
            },
            headers={
                "Authorization": f"Bearer {build_jwt_token(scopes)}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response.data
        personen = response.json()["personen"]
        expect = [person1] if hide else [person1, person2]
        assert personen == expect

        if hide:
            assert any(
                m.startswith("Removed 1 persons from response") for m in caplog.messages
            ), caplog.messages

    @pytest.mark.parametrize("can_see_bsn", [True, False])
    def test_log_retrieved_bsns(
        self, api_client, requests_mock, caplog, monkeypatch, can_see_bsn, common_headers
    ):
        """Prove that retrieved BSNs are always logged.

        Even when the user doesn't have access to that field, or won't request it,
        the field will still be included in the logs - but not returned in the response.
        """
        if not can_see_bsn:
            monkeypatch.setitem(
                BrpPersonenView.parameter_ruleset_by_type["ZoekMetPostcodeEnHuisnummer"],
                "fields",
                ParameterPolicy(
                    scopes_for_values={"naam.geslachtsnaam": {"unittest-gegevensset-1"}},
                    default_scope=None,
                ),
            )

        requests_mock.post(
            "/lap/api/brp",
            json={
                "type": "ZoekMetPostcodeEnHuisnummer",
                "personen": [
                    {
                        "naam": {"geslachtsnaam": "DUMMY_REMOVED1"},
                        "burgerservicenummer": "999993240",
                    },
                    {
                        "naam": {"geslachtsnaam": "DUMMY_REMOVED2"},
                        "burgerservicenummer": "999993252",
                    },
                ],
            },
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-personen")
        scopes = [
            "benk-brp-personen-api",
            "benk-brp-zoekvraag-postcode-huisnummer",
            ("unittest-gegevensset-1" if not can_see_bsn else "benk-brp-gegevensset-1"),
        ]
        response = api_client.post(
            url,
            {
                "type": "ZoekMetPostcodeEnHuisnummer",
                "postcode": "1074VE",
                "huisnummer": 1,
                "fields": ["naam.geslachtsnaam"],
            },
            headers={
                "Authorization": f"Bearer {build_jwt_token(scopes)}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response.data
        response = response.json()

        assert response == {
            "type": "ZoekMetPostcodeEnHuisnummer",
            "personen": [
                # burgerservicenummer retrieved from endpoint, but stripped before sending response
                {
                    "naam": {"geslachtsnaam": "DUMMY_REMOVED1"},
                },
                {
                    "naam": {"geslachtsnaam": "DUMMY_REMOVED2"},
                },
            ],
        }
        log_messages = caplog.messages
        for log_message in [
            "User doesn't request ID field burgerservicenummer, only adding for internal logging",
            "Removing additional identifier fields from response: burgerservicenummer",
            (
                "User text@example.com retrieved using 'personen.ZoekMetPostcodeEnHuisnummer':"
                " aNummer=? burgerservicenummer=999993240"
            ),
            (
                "User text@example.com retrieved using 'personen.ZoekMetPostcodeEnHuisnummer':"
                " aNummer=? burgerservicenummer=999993252"
            ),
        ]:
            assert log_message in log_messages

    def test_encrypt_decrypt_bsn(self, api_client, requests_mock, caplog, common_headers):
        """Prove encryption/decryption of BSNs works."""
        requests_mock.post(
            "/haalcentraal/api/brp/personen",
            json=self.RESPONSE_ENCRYPT_BSN,
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-personen")
        token = build_jwt_token(
            [
                "benk-brp-personen-api",
                "benk-brp-zoekvraag-postcode-huisnummer",
                "benk-brp-zoekvraag-bsn",
                "benk-brp-gegevensset-1",
                "benk-brp-encrypt-bsn",
            ]
        )
        response = api_client.post(
            f"{url}?resultaatFormaat=volledig",
            {
                "type": "ZoekMetPostcodeEnHuisnummer",
                "postcode": "1074VE",
                "huisnummer": 1,
                # No fields, is autofilled with all options of gegevensset-1.
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response.data
        response = response.json()

        # Expect BSN to be encrypted
        burgerservicenummer = response["personen"][0]["burgerservicenummer"]
        assert burgerservicenummer != "999993367"

        # Test to see if the encrypted bsn can be used in subsequent calls
        requests_mock.reset_mock()
        token = build_jwt_token(
            [
                "benk-brp-personen-api",
                "benk-brp-zoekvraag-postcode-huisnummer",
                "benk-brp-zoekvraag-bsn",
                "benk-brp-gegevensset-1",
                "benk-brp-encrypt-bsn",
            ]
        )
        response = api_client.post(
            f"{url}?resultaatFormaat=volledig",
            {
                "type": "RaadpleegMetBurgerservicenummer",
                "burgerservicenummer": [burgerservicenummer],
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response.data

        # Get the last call to the API to see if we've successfully decrypted the BSN
        request_data = requests_mock.request_history[0].json()
        assert request_data["burgerservicenummer"][0] == "999993367"

        # Expect the unencrypted bsn to show up in the logs
        log_messages = caplog.messages
        for log_message in [
            (
                "User text@example.com retrieved using 'personen.ZoekMetPostcodeEnHuisnummer':"
                " aNummer=? burgerservicenummer=999993367"
            ),
            (
                "User text@example.com retrieved using 'personen.RaadpleegMetBurgerservicenummer':"
                " aNummer=? burgerservicenummer=999993367"
            ),
        ]:
            assert log_message in log_messages

    def test_encryption_salt_required(self, api_client, requests_mock, caplog, common_headers):
        """Prove that the correlation id is used as a salt to encrypt/decrypt"""
        requests_mock.post(
            "/haalcentraal/api/brp/personen",
            json=self.RESPONSE_ENCRYPT_BSN,
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-personen")
        token = build_jwt_token(
            [
                "benk-brp-personen-api",
                "benk-brp-zoekvraag-postcode-huisnummer",
                "benk-brp-zoekvraag-bsn",
                "benk-brp-gegevensset-1",
                "benk-brp-encrypt-bsn",
            ]
        )
        response = api_client.post(
            f"{url}?resultaatFormaat=volledig",
            {
                "type": "ZoekMetPostcodeEnHuisnummer",
                "postcode": "1074VE",
                "huisnummer": 1,
                # No fields, is autofilled with all options of gegevensset-1.
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 200, response.data
        response = response.json()

        # Expect BSN to be encrypted
        burgerservicenummer = response["personen"][0]["burgerservicenummer"]
        assert burgerservicenummer != "999993367"

        caplog.clear()

        # Test to see if the encrypted bsn can not be used by another request/correlation id
        requests_mock.reset_mock()
        token = build_jwt_token(
            [
                "benk-brp-personen-api",
                "benk-brp-zoekvraag-postcode-huisnummer",
                "benk-brp-zoekvraag-bsn",
                "benk-brp-gegevensset-1",
                "benk-brp-encrypt-bsn",
            ]
        )
        common_headers["X-Correlation-ID"] = "some-correlation-id"

        response = api_client.post(
            f"{url}?resultaatFormaat=volledig",
            {
                "type": "RaadpleegMetBurgerservicenummer",
                "burgerservicenummer": [burgerservicenummer],
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 403, response.data
        assert response.json()["detail"], "Geen toegang tot versleutelde waarde."

        # Expect permission denied and the SCOPE_ENCRYPT_BSN to show up in the logs
        access_denied_message = (
            "Denied access to 'personen.RaadpleegMetBurgerservicenummer' "
            "for unencrypted burgerservicenummer with scopes"
        )

        log_messages = caplog.messages
        assert any(
            m.startswith(access_denied_message) and SCOPE_ENCRYPT_BSN in m for m in log_messages
        )

    def test_decrypt_unencrypted_bsn(self, api_client, requests_mock, caplog, common_headers):
        """Prove that not having access to a set is handled gracefully."""
        requests_mock.post(
            "/haalcentraal/api/brp/personen",
            json=self.RESPONSE_ENCRYPT_BSN,
            headers={"content-type": "application/json"},
        )

        url = reverse("brp-personen")
        token = build_jwt_token(
            [
                "benk-brp-personen-api",
                "benk-brp-zoekvraag-postcode-huisnummer",
                "benk-brp-zoekvraag-bsn",
                "benk-brp-gegevensset-1",
                "benk-brp-encrypt-bsn",
            ]
        )
        response = api_client.post(
            f"{url}?resultaatFormaat=volledig",
            {
                "type": "RaadpleegMetBurgerservicenummer",
                "burgerservicenummer": ["999993367"],
            },
            headers={
                "Authorization": f"Bearer {token}",
                **common_headers,
            },
        )
        assert response.status_code == 403, response.data

        # Expect permission denied and the SCOPE_ENCRYPT_BSN to show up in the logs
        access_denied_message = (
            "Denied access to 'personen.RaadpleegMetBurgerservicenummer' "
            "for unencrypted burgerservicenummer with scopes"
        )

        log_messages = caplog.messages
        assert any(
            m.startswith(access_denied_message) and SCOPE_ENCRYPT_BSN in m for m in log_messages
        )


def test_group_dotted_names():
    """Test whether the nested ?_expandScope can be parsed to a tree."""
    result = _group_dotted_names(
        [
            "user",
            "user.group",
            "user.permissions",
            "group",
            "group.permissions",
        ]
    )
    assert result == {
        "user": {
            "group": {},
            "permissions": {},
        },
        "group": {
            "permissions": {},
        },
    }
