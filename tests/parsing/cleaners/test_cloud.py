"""Cloud cleaner tests."""

import pytest

from avwx.parsing.sanitization.cleaners.cloud import separate_cloud_layers


@pytest.mark.parametrize(
    ("item", "clean"),
    [("TSFEW004SCT012FEW///CBBKN080", "TS FEW004 SCT012 FEW///CB BKN080")],
)
def test_separate_cloud_layers(item: str, clean: str) -> None:
    assert separate_cloud_layers(item) == clean
