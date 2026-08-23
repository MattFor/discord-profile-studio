class StudioError(Exception):
    pass


class ConfigError(StudioError):
    pass


class StorageError(StudioError):
    pass


class FavouriteNotFoundError(StorageError):
    pass


class RpcError(StudioError):
    pass


class DiscordUnavailableError(RpcError):
    pass


class ValidationError(StudioError):
    pass


class AuthError(StudioError):
    pass


class TokenNotFoundError(AuthError):
    pass


class TokenExpiredError(AuthError):
    pass


class StoreLockedError(AuthError):
    pass


class TrayUnavailableError(StudioError):
    pass


class AutostartError(StudioError):
    pass


class AlreadyRunningError(StudioError):
    pass
