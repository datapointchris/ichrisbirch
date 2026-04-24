"""Tests for UrlImport* schemas — validates kind/payload consistency rules."""

import pytest
from pydantic import ValidationError

from ichrisbirch.schemas.recipe import CookingTechniqueCreate
from ichrisbirch.schemas.recipe import RecipeCandidate
from ichrisbirch.schemas.recipe import UrlImportCandidate
from ichrisbirch.schemas.recipe import UrlImportRequest


def _recipe_payload() -> RecipeCandidate:
    return RecipeCandidate(
        name='Classic Chimichurri',
        source_url='https://www.youtube.com/watch?v=qEb96qFi2Tc',
        instructions='Chop herbs, mix vinaigrette, rest overnight.',
    )


def _technique_payload() -> CookingTechniqueCreate:
    return CookingTechniqueCreate(
        name='3:1 Vinaigrette Ratio',
        category='composition_and_ratio',
        summary='Three parts fat to one part acid is the baseline vinaigrette.',
        body='The 3:1 ratio balances richness against brightness...',
    )


class TestUrlImportRequest:
    def test_default_hint_is_auto(self):
        req = UrlImportRequest(url='https://example.com')
        assert req.hint == 'auto'

    @pytest.mark.parametrize('hint', ['auto', 'recipe', 'technique', 'both'])
    def test_valid_hints_parse(self, hint: str):
        req = UrlImportRequest(url='https://example.com', hint=hint)
        assert req.hint == hint

    def test_invalid_hint_rejected(self):
        with pytest.raises(ValidationError):
            UrlImportRequest(url='https://example.com', hint='banana')


class TestUrlImportCandidateKindValidation:
    def test_recipe_kind_with_recipe_is_valid(self):
        c = UrlImportCandidate(kind='recipe', recipe=_recipe_payload())
        assert c.recipe is not None
        assert c.technique is None

    def test_recipe_kind_without_recipe_rejected(self):
        with pytest.raises(ValidationError, match='kind=recipe requires'):
            UrlImportCandidate(kind='recipe')

    def test_technique_kind_with_technique_is_valid(self):
        c = UrlImportCandidate(kind='technique', technique=_technique_payload())
        assert c.technique is not None
        assert c.recipe is None

    def test_technique_kind_without_technique_rejected(self):
        with pytest.raises(ValidationError, match='kind=technique requires'):
            UrlImportCandidate(kind='technique')

    def test_both_kind_with_both_payloads_is_valid(self):
        c = UrlImportCandidate(
            kind='both',
            recipe=_recipe_payload(),
            technique=_technique_payload(),
            technique_mention='Uses the 3:1 vinaigrette ratio technique',
        )
        assert c.recipe is not None
        assert c.technique is not None
        assert c.technique_mention == 'Uses the 3:1 vinaigrette ratio technique'

    def test_both_kind_missing_recipe_rejected(self):
        with pytest.raises(ValidationError, match='kind=both requires'):
            UrlImportCandidate(kind='both', technique=_technique_payload())

    def test_both_kind_missing_technique_rejected(self):
        with pytest.raises(ValidationError, match='kind=both requires'):
            UrlImportCandidate(kind='both', recipe=_recipe_payload())

    def test_technique_mention_is_optional_even_for_both(self):
        c = UrlImportCandidate(kind='both', recipe=_recipe_payload(), technique=_technique_payload())
        assert c.technique_mention is None
