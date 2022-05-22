from enum import Enum

from typing import TYPE_CHECKING, Any, Optional, Tuple, Type

from pydantic import BaseModel, StrictBool, StrictStr, constr, validator

# Ugly workaround for https://github.com/samuelcolvin/pydantic/issues/156. Mypy doesn't
# consider expressions like `constr(...)` to be valid types.
from pydantic.fields import ModelField

from synapse.util.stringutils import parse_and_validate_mxc_uri

if TYPE_CHECKING:
    IDP_ID_TYPE = str
    IDP_BRAND_TYPE = str
else:
    IDP_ID_TYPE = constr(
        strict=True,
        min_length=1,
        max_length=250,
        regex="^[A-Za-z0-9._~-]+$",  # noqa: F722
    )
    IDP_BRAND_TYPE = constr(
        strict=True,
        min_length=1,
        max_length=255,
        regex="^[a-z][a-z0-9_.-]*$",  # noqa: F722
    )

# the following list of enum members is the same as the keys of
# authlib.oauth2.auth.ClientAuth.DEFAULT_AUTH_METHODS. We inline it
# to avoid importing authlib here.
class ClientAuthMethods(str, Enum):
    # The duplication is unfortunate. 3.11 should have StrEnum though,
    # and there is a backport available for 3.8.6.
    client_secret_basic = "client_secret_basic"
    client_secret_post = "client_secret_post"
    none = "none"


class UserProfileMethod(str, Enum):
    # The duplication is unfortunate. 3.11 should have StrEnum though,
    # and there is a backport available for 3.8.6.
    auto = "auto"
    userinfo_endpoint = "userinfo_endpoint"


class OIDCProviderModel(BaseModel):
    """
    Notes on Pydantic:
    - I've used StrictStr because a plain `str` e.g. accepts integers and calls str()
      on them
    - pulling out constr() into IDP_ID_TYPE is a little awkward, but necessary to keep
      mypy happy
    -
    """

    # a unique identifier for this identity provider. Used in the 'user_external_ids'
    # table, as well as the query/path parameter used in the login protocol.
    idp_id: IDP_ID_TYPE

    @validator("idp_id")
    def ensure_idp_id_prefix(cls: Type[BaseModel], idp_id: str) -> str:
        """Prefix the given IDP with a prefix specific to the SSO mechanism, to avoid
        clashes with other mechs (such as SAML, CAS).

        We allow "oidc" as an exception so that people migrating from old-style
        "oidc_config" format (which has long used "oidc" as its idp_id) can migrate to
        a new-style "oidc_providers" entry without changing the idp_id for their provider
        (and thereby invalidating their user_external_ids data).
        """
        if idp_id != "oidc":
            return "oidc-" + idp_id
        return idp_id

    # user-facing name for this identity provider.
    idp_name: StrictStr

    # Optional MXC URI for icon for this IdP.
    idp_icon: Optional[StrictStr]

    @validator("idp_icon")
    def idp_icon_is_an_mxc_url(cls: Type["OIDCProviderModel"], value: str) -> str:
        parse_and_validate_mxc_uri(value)
        return value

    # Optional brand identifier for this IdP.
    idp_brand: Optional[StrictStr]

    # whether the OIDC discovery mechanism is used to discover endpoints
    discover: StrictBool = True

    # the OIDC issuer. Used to validate tokens and (if discovery is enabled) to
    # discover the provider's endpoints.
    issuer: StrictStr

    # oauth2 client id to use
    client_id: StrictStr

    # oauth2 client secret to use. if `None`, use client_secret_jwt_key to generate
    # a secret.
    client_secret: Optional[StrictStr]

    # key to use to construct a JWT to use as a client secret. May be `None` if
    # `client_secret` is set.
    # TODO
    client_secret_jwt_key: Optional[Any]  # OidcProviderClientSecretJwtKey]

    # auth method to use when exchanging the token.
    # Valid values are 'client_secret_basic', 'client_secret_post' and
    # 'none'.
    client_auth_method: ClientAuthMethods = ClientAuthMethods.client_secret_basic

    # list of scopes to request
    scopes: Tuple[StrictStr, ...] = ("openid",)

    # the oauth2 authorization endpoint. Required if discovery is disabled.
    authorization_endpoint: Optional[StrictStr]

    # the oauth2 token endpoint. Required if discovery is disabled.
    token_endpoint: Optional[StrictStr]

    # Normally, validators aren't run when fields don't have a value provided.
    # Using validate=True ensures we run the validator even in that situation.
    @validator("authorization_endpoint", "token_endpoint", always=True)
    def endpoints_required_if_discovery_disabled(
        cls: Type["OIDCProviderModel"],
        endpoint_url: Optional[str],
        values: Mapping[str, Any],
        field: ModelField,
    ) -> Optional[str]:
        # `if "discover" in values means: don't run our checks if "discover" didn't
        # pass validation. (NB: validation order is the field definition order)
        if "discover" in values and not values["discover"] and endpoint_url is None:
            raise ValueError(f"{field.name} is required if discovery is disabled")
        return endpoint_url

    # the OIDC userinfo endpoint. Required if discovery is disabled and the
    # "openid" scope is not requested.
    # TODO: required if discovery is disabled and the openid scope isn't requested
    userinfo_endpoint: Optional[StrictStr]

    # URI where to fetch the JWKS. Required if discovery is disabled and the
    # "openid" scope is used.
    # TODO: required if discovery is disabled and the openid scope IS requested
    jwks_uri: Optional[StrictStr]

    # Whether to skip metadata verification
    skip_verification: StrictBool = False

    # Whether to fetch the user profile from the userinfo endpoint. Valid
    # values are: "auto" or "userinfo_endpoint".
    user_profile_method: UserProfileMethod = UserProfileMethod.auto

    # whether to allow a user logging in via OIDC to match a pre-existing account
    # instead of failing
    allow_existing_users: StrictBool = False

    # the class of the user mapping provider
    # TODO
    user_mapping_provider_class: Any  # TODO: Type

    # the config of the user mapping provider
    # TODO
    user_mapping_provider_config: Any

    # required attributes to require in userinfo to allow login/registration
    attribute_requirements: Tuple[Any, ...] = ()  # TODO SsoAttributeRequirement] = ()


class LegacyOIDCProviderModel(OIDCProviderModel):
    idp_id: IDP_ID_TYPE = "oidc"
    idp_name: StrictStr = "OIDC"