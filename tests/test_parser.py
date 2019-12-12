import re
from unittest import mock

import pytest

from avwx.parsing import Parser, AtomHandler, BaseAtom, RegexAtom
from avwx.parsing.exceptions import TranslationError


SAMPLE_STRING = """TH1S 1S AN 3NC0D3D STRING"""


class TestParser:
    def test_iter_handlers_that_can_handle_string(self):
        parser = Parser()

        handler_1 = mock.MagicMock(spec=AtomHandler)
        handler_2 = mock.MagicMock(spec=AtomHandler)
        handler_3 = mock.MagicMock(spec=AtomHandler)

        handler_1.can_handle.return_value = True
        handler_2.can_handle.return_value = False
        handler_3.can_handle.return_value = True

        parser.register_handler(handler_1)
        parser.register_handler(handler_2)
        parser.register_handler(handler_3)

        handlers = list(parser._iter_handlers_that_can_handle_string(SAMPLE_STRING))

        assert handlers == [handler_1, handler_3]


class TestParsingIntegration:
    BASE_EXPECTED = {
        "TH1S 1S": "THIS IS: 1",
        "AN 3NC0D3D": "AN ENCODED: 303",
        "STRING": "STRING",
    }

    def make_parser(self):
        atom_1 = RegexAtom.from_pattern_string("TH1S 1S")
        atom_2 = RegexAtom.from_pattern_string("AN 3NC0D3D")
        atom_3 = RegexAtom.from_pattern_string("STRING")
        atom_4 = RegexAtom.from_pattern_string("NOT PRESENT")

        handler_1 = AtomHandler(atom_1, lambda atom, string: "THIS IS: 1")
        handler_2 = AtomHandler(atom_2, lambda atom, string: "AN ENCODED: 303")
        handler_3 = AtomHandler(atom_3, lambda atom, string: "STRING")
        handler_4 = AtomHandler(atom_4, lambda atom, string: "NOPE")

        parser = Parser()

        for handler in [handler_4, handler_3, handler_2, handler_1]:
            parser.register_handler(handler)

        return parser

    def test_parse_into_translations(self):
        parser = self.make_parser()

        translations = parser.parse_into_translations(SAMPLE_STRING)

        expected = {
            "TH1S 1S": "THIS IS: 1",
            "AN 3NC0D3D": "AN ENCODED: 303",
            "STRING": "STRING",
        }

        assert translations == expected

    def test_strict_parse_into_translations(self):
        parser = self.make_parser()

        bad_atom = mock.MagicMock()
        bad_atom.name = "BAD ATOM"
        bad_handler = AtomHandler(bad_atom, lambda a, s: "should do nothing")
        bad_handler.can_handle = mock.MagicMock(return_value=True)
        bad_handler.translate = mock.MagicMock(side_effect=TranslationError("no"))

        parser.register_handler(bad_handler)

        with pytest.raises(TranslationError, match="no") as exc_info:
            result = parser.parse_into_translations(SAMPLE_STRING, strict=True)

        expected = self.BASE_EXPECTED.copy()
        expected.update({"BAD ATOM": "ERROR: " + "no"})

        result = parser.parse_into_translations(SAMPLE_STRING, strict=False)

        assert expected == result

    def test_register_unregister_handler(self):
        parser = self.make_parser()

        handler = mock.MagicMock(spec=AtomHandler)

        parser.register_handler(handler)

        assert handler in parser.handlers

        parser.unregister_handler(handler)

        assert not handler in parser.handlers
