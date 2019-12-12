import pytest
import re
from unittest import mock

from avwx.parsing.atom import AtomSpan, RegexAtom, BaseAtom


@pytest.fixture
def pattern_string():
    return r"\bSOME PATTERN P(?P<digits>\d{1,5})\b"


@pytest.fixture
def pattern(pattern_string):
    return re.compile(pattern_string)


@pytest.fixture
def regex_atom(pattern):
    return RegexAtom(pattern, name="Some Pattern")


SUCCESS_STRING = "HERE IS SOME PATTERN P123 THING"
FAIL_STRING = "YOU HAVE NO MATCH HERE"


@pytest.fixture
def base_atom_subclass():
    class SubAtom(BaseAtom):
        def to_atom_span(self, item: str) -> AtomSpan:
            raise NotImplementedError("tests should mock this")

    return SubAtom


@pytest.fixture
def mocked_atom_subclass(base_atom_subclass):
    mock_to_atom_span = mock.MagicMock()
    base_atom_subclass.to_atom_span = mock_to_atom_span

    return base_atom_subclass


@pytest.fixture
def mocked_atom_instance(mocked_atom_subclass):
    atom = mocked_atom_subclass("sample atom")
    return atom


class TestBaseAtom:
    def test_constructor(self, base_atom_subclass):
        sub = base_atom_subclass("base atom")
        assert sub.name == "base atom"

    def test_is_in(self, mocked_atom_instance):
        atom = mocked_atom_instance
        atom.to_atom_span.return_value.match = "something"

        assert atom.is_in("string")

    def test_is_in_returns_false(self, mocked_atom_instance):
        atom = mocked_atom_instance
        atom.to_atom_span.return_value.match = None

        assert not atom.is_in("string")

    def test_find_atom_in_string(self, mocked_atom_instance):
        atom = mocked_atom_instance
        atom.to_atom_span.return_value.match = "string"

        assert atom.find_atom_in_string("this is a string") == "string"

    def test_find_atom_in_string_return_none(self, mocked_atom_instance):
        atom = mocked_atom_instance
        atom.to_atom_span.return_value.match = None

        assert atom.find_atom_in_string("this is a string") is None

    def test_extract_atom_from_string(self, mocked_atom_instance):
        s = "012345string23456789"

        atom = mocked_atom_instance
        atom.to_atom_span.return_value = AtomSpan(
            match="string", start=6, end=12, context={},
        )

        assert ("string", "01234523456789") == atom.extract_atom_from_string(s)

    def test_extract_atom_from_string_raises(self, mocked_atom_subclass):
        atom = mocked_atom_subclass(name="some atom")
        atom.to_atom_span.return_value = AtomSpan(None, None, None, None)

        with pytest.raises(ValueError) as exc_info:
            atom.extract_atom_from_string("some string")

        assert "Atom: 'some atom' not in 'some string'" in str(exc_info.value)


class TestRegexAtom:
    def test_constructor(self, regex_atom, pattern):
        atom = regex_atom
        assert atom is not None
        assert atom.regex == pattern
        assert isinstance(atom._regex, re.Pattern)
        assert atom.name == "Some Pattern"

    def test_to_atom_span(self, regex_atom):
        exp = AtomSpan(
            match="SOME PATTERN P123", start=8, end=25, context={"digits": "123"}
        )
        match, start, end, context = regex_atom.to_atom_span(SUCCESS_STRING)

        assert regex_atom.to_atom_span(SUCCESS_STRING) == exp
        assert SUCCESS_STRING[start:end] == match

    def test_is_in(self, regex_atom):
        assert regex_atom.is_in(SUCCESS_STRING)

    def test_from_pattern_string(self, pattern_string):
        atom = RegexAtom.from_pattern_string(pattern_string, name="some pattern")

        assert atom.is_in(SUCCESS_STRING)
        assert not atom.is_in(FAIL_STRING)

    def test_from_pattern_string_with_flag(self, pattern_string):
        string_parts = pattern_string.split()
        string_parts[0] = string_parts[0].lower()

        lower_string = " ".join(string_parts)

        atom = RegexAtom.from_pattern_string(lower_string, re.I, re.M)

        assert atom.is_in(SUCCESS_STRING)
        assert not atom.is_in(FAIL_STRING)
