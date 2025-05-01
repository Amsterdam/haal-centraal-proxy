from django.conf import settings

from haal_centraal_proxy.bevragingen.permissions import ParameterPolicy

from .base import BaseProxyView


class BrpBewoningenView(BaseProxyView):
    """View to proxy Haal Centraal Bewoning (ocupancy).

    See: https://brp-api.github.io/Haal-Centraal-BRP-bewoning/
    """

    service_log_id = "bewoningen"
    endpoint_url = settings.BRP_BEWONINGEN_URL

    # Require extra scopes
    needed_scopes = {"benk-brp-bewoning-api"}

    # Validate the access to various parameters:
    parameter_ruleset = {
        "type": ParameterPolicy(
            scopes_for_values={
                "BewoningMetPeildatum": {"benk-brp-bewoning-api"},
                "BewoningMetPeriode": {"benk-brp-bewoning-api"},
            }
        ),
        "adresseerbaarObjectIdentificatie": ParameterPolicy.allow_all,  # used for both types.
        "peildatum": ParameterPolicy.allow_all,  # for BewoningMetPeildatum
        "datumTot": ParameterPolicy.allow_all,  # for BewoningMetPeriode
        "datumVan": ParameterPolicy.allow_all,  # for BewoningMetPeriode
    }
