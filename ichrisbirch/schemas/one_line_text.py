"""Text read on one line, such as a title: every run of whitespace becomes one space.

A title pasted from a page arrives carrying the page's newlines, tabs and
indentation. Stored as typed, it prints across several lines and sorts ahead of
every letter, so it is collapsed on the way in. Text that is all whitespace is
refused rather than stored empty.
"""

from typing import Annotated

from pydantic import AfterValidator


def collapse_to_one_line(value: str) -> str:
    collapsed = ' '.join(value.split())
    if not collapsed:
        raise ValueError('must contain text')
    return collapsed


OneLineText = Annotated[str, AfterValidator(collapse_to_one_line)]
