import pytest
from unittest import mock
from collections import OrderedDict

from avwx.parsing.atom_handlers import AtomHandler, BaseAtom
from avwx.parsing.atom import AtomSpan
from avwx.parsing.exceptions import CanNotHandleError

SAMPLE_STRING = "THIS IS A SAMPLE STRING WITH 3NC0D3D DATA"


def translate_sample_string(span: AtomSpan, string: str) -> str:
    context = span.context or {}

    context_od = OrderedDict(**context)

    context_str = f" context: {str(list(context_od.values()))}" if context_od else ""

    return f"Decoded: 303{context_str}"


@pytest.fixture
def mocked_atom_handler() -> AtomHandler:
    """
    AtomHandler with a mocked atom that can be configured before
    handler test calls. The translation callable simply returns
    "Decoded: 303" and should be mocked for different behaviors.

    Default mocked calls:
        * atom.name = "Sample Atom"
    """
    mock_atom = mock.MagicMock()
    mock_atom.name = "Sample Atom"

    handler = AtomHandler(mock_atom, translate_sample_string)

    return handler


class TestAtomHandler:
    def test_can_handle(self, mocked_atom_handler):
        handler = mocked_atom_handler
        handler.atom.is_in.return_value = True

        assert handler.can_handle(SAMPLE_STRING)

        handler.atom.is_in.return_value = False

        assert not handler.can_handle(SAMPLE_STRING)

    def test_translation_handler_signature(self, mocked_atom_handler):
        """Test that the translation is strictly called with the correct signature"""
        handler = mocked_atom_handler
        handler.atom.is_in.return_value = True

        mock_translation = mock.MagicMock(return_value=SAMPLE_STRING)
        handler.translation_callable = mock_translation

        _ = handler.translate(SAMPLE_STRING)

        mocked_atom_handler.translation_callable.assert_called_with(
            handler.atom.to_atom_span(), SAMPLE_STRING,
        )

    def test_translate_atom(self, mocked_atom_handler):
        handler = mocked_atom_handler
        handler.atom.is_in.return_value = True

        result = handler.translate(SAMPLE_STRING)

        assert result == "Decoded: 303" == handler(SAMPLE_STRING)

    def test_translate_atom_raises_for_can_not_handle(self, mocked_atom_handler):
        handler = mocked_atom_handler
        handler.atom.is_in.return_value = False

        with pytest.raises(CanNotHandleError) as exc_info:
            result = handler.translate(SAMPLE_STRING)

        expected = f"{handler.atom!r} has nothing to translate from {SAMPLE_STRING!r}"

        assert expected in str(exc_info.value)

    def test_create_simple_translation(self, mocked_atom_handler):
        match = "THIS IS A MATCH"
        output = "OUTPUT"
        mock_atom = mock.MagicMock(spec=BaseAtom)
        mock_atom.to_atom_span.return_value.match = match

        handler = AtomHandler.create_simple_translation(mock_atom, output, "simple")

        assert handler.translate("THIS IS A MOCKED") == "OUTPUT"
