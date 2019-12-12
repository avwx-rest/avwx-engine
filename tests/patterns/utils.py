import re
from pprint import pformat


def assert_match(pattern: re.Pattern, inp: str, should_match: bool):
    """
    Assert the pattern results in a match when searched with inp.
    `should_match` can be True to negate the assertion.
    """
    match = pattern.search(inp)
    if should_match:
        assert match, match
    else:
        assert match is None, match


def assert_group_dict(pattern: re.Pattern, inp: str, expected_dict: dict):
    """Assert the pattern matches group dict from input"""
    match = pattern.search(inp)

    assert match is not None, f"No match upon search... result:\n{match}"

    gp_dct = match.groupdict()

    error_message = f"EXPECTED: \n{pformat(expected_dict)}\nGOT: \n{pformat(gp_dct)}"

    for exp_k, exp_v in expected_dict.items():
        assert gp_dct.get(exp_k) == exp_v, error_message
