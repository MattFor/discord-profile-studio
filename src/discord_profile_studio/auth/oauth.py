from discord_profile_studio.auth.token import Token

DEFAULT_SCOPES = ("identify", "rpc")
TOKEN_URL = "https://discord.com/api/oauth2/token"
AUTHORIZE_URL = "https://discord.com/oauth2/authorize"


class OAuthFlow:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def authorize_url(self, scopes: tuple[str, ...] = DEFAULT_SCOPES) -> str:
        raise NotImplementedError

    def exchange(self, code: str) -> Token:
        raise NotImplementedError

    def refresh(self, token: Token) -> Token:
        raise NotImplementedError

    def revoke(self, token: Token) -> None:
        raise NotImplementedError
