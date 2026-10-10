"""Errors that must stop a scan instead of being retried per item."""

# A bad key, missing permission or retired model fails every call; retrying wastes quota.
_FATAL = {"AuthenticationError", "PermissionDeniedError", "NotFoundError"}


def is_fatal(exc: BaseException) -> bool:
    return type(exc).__name__ in _FATAL
