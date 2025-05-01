from django.conf import settings

from haal_centraal_proxy.bevragingen.permissions import ParameterPolicy

from .base import BaseProxyView


class BrpVerblijfplaatshistorieView(BaseProxyView):
    """View that proxies Haal Centraal BRP Verblijfplaatshistorie of a person (residence history).

    See: https://brp-api.github.io/Haal-Centraal-BRP-historie-bevragen/
    """

    service_log_id = "verblijfplaatshistorie"
    endpoint_url = settings.BRP_VERBLIJFPLAATSHISTORIE_URL

    # Require extra scopes
    needed_scopes = {"benk-brp-verblijfplaatshistorie-api"}

    # A quick dictionary to automate permission-based access to certain filter parameters.
    parameter_ruleset = {
        "type": ParameterPolicy(
            scopes_for_values={
                "RaadpleegMetPeildatum": {"benk-brp-verblijfplaatshistorie-api"},
                "RaadpleegMetPeriode": {"benk-brp-verblijfplaatshistorie-api"},
            }
        ),
        "burgerservicenummer": ParameterPolicy.allow_all,  # used for both request types.
        "peildatum": ParameterPolicy.allow_all,  # for RaadpleegMetPeildatum
        "datumTot": ParameterPolicy.allow_all,  # for RaadpleegMetPeriode
        "datumVan": ParameterPolicy.allow_all,  # for RaadpleegMetPeriode
    }
