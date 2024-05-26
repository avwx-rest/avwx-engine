"""Current Report Base Tests."""

# library
import pytest

# module
from avwx import current
from avwx.structs import Code


@pytest.mark.parametrize(
    ("code", "value"),
    [
        ("+RATS", "Heavy Rain Thunderstorm"),
        ("VCFC", "Vicinity Funnel Cloud"),
        ("-GR", "Light Hail"),
        ("FZFG", "Freezing Fog"),
        ("BCBLSN", "Patchy Blowing Snow"),
    ],
)
def test_wxcode(code: str, value: str) -> None:
    """Test expanding weather codes or ignoring them."""
    obj = Code(code, value)
    assert current.base.wx_code(code) == obj


@pytest.mark.parametrize(
    ("code", "value"),
    [("", ""), ("R03/03002V03", "R03/03002V03"), ("CB", "CB"), ("0800SE", "0800SE")],
)
def test_unknown_code(code: str, value: str) -> None:
    assert current.base.wx_code(code) == value
