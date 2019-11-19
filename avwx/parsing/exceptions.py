"""
Exceptions for 'parsing' package
"""


class AtomHandlerException(Exception):
    """Base Exception for `AtomHandler` operations"""

    pass


class CanNotHandleError(AtomHandlerException):
    """Can not execute translation due to bad match"""

    pass


class TranslationError(AtomHandlerException):
    """Unexpected error occurred during translation"""

    pass
