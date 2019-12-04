import abc
import re
from typing import Optional, NamedTuple, Tuple, Dict


# todo: add text
class AtomSpan(NamedTuple):
    """
    Finding within a string. Can be used for slicing as `end` is non-inclusive.

    'context' is a Dict[str,str] that can be used in translation functions.
    """

    match: Optional[str]
    start: Optional[int]
    end: Optional[int]
    context: Optional[Dict[str, str]]


# todo: add make_context
class BaseAtom(abc.ABC):
    """Atom represents a single encoded entity in an encoded string"""

    def __init__(self, name: str):
        self.name = name

    # todo: decorate to return an empty atom string from a False return value
    @abc.abstractmethod
    def to_atom_span(self, item: str) -> AtomSpan:
        """Return an `AtomSpan`. If no match found, return `AtomSpan(None, None, None)`"""
        pass

    def find_atom_in_string(self, string: str) -> Optional[str]:
        """Return the matching atom from a string"""
        return self.to_atom_span(string).match

    def is_in(self, string: str) -> bool:
        """Return True if the atom is in the string"""
        return self.find_atom_in_string(string) is not None

    # todo: add strip
    def extract_atom_from_string(self, string: str) -> Tuple[str, str]:
        """
        Return extracted atom and string with atom extracted

        For instance, if the atom were "some string" and the input were
        "this is some string I have"..

        return -> "some string", "this is  I have"
        """
        span = self.to_atom_span(string)
        if span.start is None or span.end is None:
            raise ValueError(f"Atom: '{self.name}' not in '{string}'")
        else:
            match = span.match or ""
            extract = string[: span.start] + string[span.end :]

            return match, extract


# todo: enforce name
class RegexAtom(BaseAtom):
    """Atom defined by regex pattern"""

    def __init__(self, regex_pattern: re.Pattern, name: str):
        self.regex = regex_pattern
        super().__init__(name)

    def __repr__(self):
        return f"{type(self).__name__}(pattern={self.regex!r}, name={self.name})"

    @property
    def regex(self) -> re.Pattern:
        return self._regex

    @regex.setter
    def regex(self, regex: re.Pattern):
        if not isinstance(regex, re.Pattern):
            raise TypeError("regex must be a compiled `re.Pattern`")
        self._regex = regex

    # fixme: name should NOT be optional
    @classmethod
    def from_pattern_string(
        cls, pattern: str, *flags: re.RegexFlag, name: Optional[str] = None
    ) -> "RegexAtom":
        """
        Return a new instance of `RegexAtom` from a string pattern.

        .. note::

            It is important to ensure that patterns are raw strings, just like
            you were creating a compiled regex pattern normally.

        .. code-block::

            aircraft_mishap_atom = RegexAtom.from_pattern_string(r"\bACFT MSHP\b")

        :param pattern: string to be compiled into regex pattern
        :param flags: flags to pass to `re.compile`
        :param name: name for repr
        """

        if flags:
            regex = re.compile(pattern, sum(flags))
        else:
            regex = re.compile(pattern)

        out = cls(regex, name=name)

        return out

    def to_atom_span(self, string: str) -> AtomSpan:
        """
        Search the string for the atom
        """
        match = self.regex.search(string)
        if match:
            start, stop = match.span()
            return AtomSpan(
                match=match.group(), start=start, end=stop, context=match.groupdict()
            )
        return AtomSpan(match=None, start=None, end=None, context={})

    # todo: remove to use context in `to_atom_span` instead
    def search(self, string: str) -> Optional[re.Match]:
        """
        Return `re.Match` object or None
        """
        return self.regex.search(string)
