from haal_centraal_proxy.settings import *  # noqa: F403, F405

# The reason the settings are defined here, is to make them independent
# of the regular project sources. Otherwise, the project needs to have
# knowledge of the test framework.

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Load public/private test key pair.
# This was obtained in the authz project with: jwkgen -create -alg ES256
jwks_key = Path(__file__).parent.parent.joinpath("jwks_test.json").read_text()

DATAPUNT_AUTHZ = {
    "JWKS": jwks_key,
    "ALWAYS_OK": False,
    "MIN_INTERVAL_KEYSET_UPDATE": 30 * 60,  # 30 minutes
}

# Remove propagate=False so caplog can read those messages.
LOGGING = {
    **LOGGING,
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
    "loggers": {
        name: {
            **conf,
            "propagate": True,
        }
        for name, conf in LOGGING["handlers"].items()
    },
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Prevent tests to crash because of missing staticfiles manifests
WHITENOISE_MANIFEST_STRICT = False
STORAGES = {
    **STORAGES,
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# use different defaults.
# By using a portnumber, the BrpClient detects that this is a mock API, and will not require OAuth.
BRP_URL = env.str("BRP_URL", default="http://localhost:5010/lap/api/brp")
BRP_PERSONEN_URL = env.str("BRP_PERSONEN_URL", default=f"{BRP_URL}/personen")
BRP_BEWONINGEN_URL = env.str("BRP_BEWONINGEN_URL", default=f"{BRP_URL}/bewoning/bewoningen")
BRP_VERBLIJFPLAATSHISTORIE_URL = env.str(
    "BRP_VERBLIJFPLAATSHISTORIE_URL", default=f"{BRP_URL}/verblijfplaatshistorie"
)
