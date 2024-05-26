"""PIREP sanitization support."""

from avwx.parsing.sanitization.base import sanitize_string_with
from avwx.parsing.sanitization.cleaners.replace import CURRENT

clean_pirep_string = sanitize_string_with(CURRENT)
