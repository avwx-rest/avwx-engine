"""
AtomHandler:
    * bundles atom and some translation callable together to be executed with arbitrary strings

TranslationCallable:
    * A client defined callable that operates on an AtomSpan and an input string

    example:


        def sea_level_pressure_translation(span, input_: str) -> str:
            match = span.match
            if not match:
                raise TranslationError("some descriptive error")
            else:
                pressure = match[3:].strip()

            return f"Sea Level Pressure {pressure}"

        -- or with a RegEx Atom --

        def sea_level_pressure_translation(span, input_: str) -> str:
            context = span.context
            if not match:
                raise TranslationError("some descriptive error")

            return f"Sea Level Pressure {data["pressure"]}"

    * TranslationError - should be raised when there is a problem during the translation.
        - This should be used instead of a ValueError so that the handler can decide what to do instead. Maybe
        a default translation or error code should be used instead for cleanup
"""

from typing import NamedTuple

from .exceptions import CanNotHandleError, TranslationError
from .atom import AtomSpan, BaseAtom
from .translation import Translation


class TranslationResult(NamedTuple):
    pass


# todo: multiple translations for a single atom?
# todo: add name enforcement
class AtomHandler:
    """Handle the individual translation of an atom"""

    def __init__(
        self, atom: BaseAtom, translation_callable: Translation, name: str = None
    ):
        self.atom = atom
        self.translation_callable = translation_callable
        self.name = name

    def __repr__(self):
        return f"{type(self).__name__}(atom: {self.atom.name})"

    def __call__(self, string: str, *args, **kwargs):
        return self.translate(string)

    @property
    def translation_callable(self):
        return self._translation_callable

    @translation_callable.setter
    def translation_callable(self, new_callable: Translation):
        if not callable(new_callable):
            raise TypeError(
                "translation_callable must be a callable that accepts a `BaseAtom` and a string"
            )
        self._translation_callable = new_callable

    @classmethod
    def create_simple_translation(
        cls, atom: BaseAtom, output: str, name: str
    ) -> "AtomHandler":
        """Return a new `AtomHandler` which will return a simple string as a translation"""

        def translation(span: AtomSpan, string: str):
            return output

        out = cls(atom, translation, name)

        return out

    def can_handle(self, atom_string: str) -> bool:
        """Return True if handler is qualified to handle translation"""
        return self.atom.is_in(atom_string)

    # todo: allow for default error handling option
    def translate(self, string: str) -> str:
        """Perform translation on the atom string"""
        span = self.atom.to_atom_span(string)
        if not self.atom.is_in(string):
            raise CanNotHandleError(
                f"{self.atom!r} has nothing to translate from {string!r}"
            )

        # todo: defer to private wrapper that handles error?
        result = self.translation_callable(span, string)

        return result
