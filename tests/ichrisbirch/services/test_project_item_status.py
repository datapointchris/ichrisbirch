"""The derived status, in both directions, from the one module that owns it.

`apply_status_filter` narrows a query to one status and `derive_item_status`
names one row's. They encode the same precedence, so the pairing is what these
tests are about: the set a filter returns has to be exactly the set whose
derived status matches it.
"""

import pytest

from ichrisbirch.models.project import ITEM_STATUSES
from ichrisbirch.services.project_item_status import derive_item_status

# The four reachable combinations of the two stored booleans, and the word each
# one answers to. Archived beats completed, so the third and fourth agree.
COMBINATIONS = [
    (False, False, 'open'),
    (False, True, 'completed'),
    (True, False, 'archived'),
    (True, True, 'archived'),
]


@pytest.mark.parametrize(('archived', 'completed', 'expected'), COMBINATIONS)
def test_each_combination_answers_to_one_word(archived, completed, expected):
    assert derive_item_status(archived=archived, completed=completed) == expected


def test_archived_beats_completed():
    """An item finished and then archived answers to archived alone."""
    assert derive_item_status(archived=True, completed=True) == 'archived'
    assert derive_item_status(archived=True, completed=True) != 'completed'


def test_every_derived_word_is_one_the_filter_accepts():
    """A row could otherwise report a status that --status refuses."""
    derived = {derive_item_status(archived=a, completed=c) for a, c, _ in COMBINATIONS}
    assert derived <= set(ITEM_STATUSES)


def test_the_three_statuses_are_all_reachable():
    """Two booleans, three states, and none of them unreachable."""
    derived = {derive_item_status(archived=a, completed=c) for a, c, _ in COMBINATIONS}
    assert derived == set(ITEM_STATUSES)
