"""
PIREP sanitization support
"""

from .cleaners.replace import CURRENT
from .base import sanitize_string_with

clean_pirep_string = sanitize_string_with(CURRENT)
