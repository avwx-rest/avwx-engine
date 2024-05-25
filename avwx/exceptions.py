"""Contains avwx custom exceptions."""


def exception_intercept(exception: Exception, **extra: dict) -> None:  # noqa: ARG001
    """Interceptor to overwrite unhandled exceptions in high-failure locations."""
    raise exception


class BadStation(Exception):
    """Station does not exist."""


class InvalidRequest(Exception):
    """Unable to fetch data."""


class SourceError(Exception):
    """Source servers returned an error code."""


class MissingExtraModule(ModuleNotFoundError):
    """Inform user that an extra install module is needed."""

    def __init__(self, extra: str):
        super().__init__(f"Install avwx-engine[{extra}] to use this feature")
