import re
from re import Pattern
from typing import List
from typing import Union


def pcre_to_python_re(regex: str) -> Pattern:
    """Converts a PCRE (Perl) to a Python-compatible regex"""
    return re.compile(regex.replace("(?<", "(?P<"))


def parse_regex(raw_regex: Union[str, List[str]]) -> Pattern:
    """Parses a single- or multi-line regex, where lines are represented
    as items in a list.
    """
    if isinstance(raw_regex, list):
        raw_regex = "".join(raw_regex)

    return pcre_to_python_re(raw_regex)
