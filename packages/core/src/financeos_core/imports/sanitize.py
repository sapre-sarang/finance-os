import re

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_WHITESPACE_RUN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Strip control characters, collapse whitespace, and defuse spreadsheet formulas.

    Statement text is later exported and opened in spreadsheets, where a leading
    '=' or '+' executes as a formula.
    """
    collapsed = _WHITESPACE_RUN.sub(" ", _CONTROL_CHARS.sub("", text)).strip()
    if collapsed.startswith(_FORMULA_PREFIXES):
        return "'" + collapsed
    return collapsed
