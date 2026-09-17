"""Tests for the URL import classifier's handling of what the assistant returns."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ichrisbirch import schemas
from ichrisbirch.ai.assistants.anthropic import AssistantFailure
from ichrisbirch.ai.assistants.anthropic import AssistantOutputError
from ichrisbirch.services.url_ingest import classify_url_content

URL = 'https://www.youtube.com/watch?v=qEb96qFi2Tc'


def patched_assistant(generate_structured: AsyncMock):
    assistant = MagicMock()
    assistant.generate_structured = generate_structured
    return patch('ichrisbirch.services.url_ingest.AnthropicAssistant', MagicMock(return_value=assistant))


@pytest.mark.asyncio
async def test_an_unusable_reply_reaches_the_caller_with_its_reason():
    """The API's handler answers the 502 from the reason, so rewrapping the error would lose it."""
    refused = AssistantOutputError(AssistantFailure.FAILED, 'failed (HTTP 401)', 'API Error: 401')
    with patched_assistant(AsyncMock(side_effect=refused)), pytest.raises(AssistantOutputError) as caught:
        await classify_url_content(URL, 'auto', 'content', MagicMock())
    assert caught.value.reason == AssistantFailure.FAILED
    assert caught.value.raw_output == 'API Error: 401'


@pytest.mark.asyncio
async def test_the_candidate_source_url_is_pinned_to_the_url_imported():
    """The duplicate check on re-import matches on source_url, and the model sometimes rewrites it."""
    recipe = schemas.RecipeCandidate(name='Chimichurri', source_url='https://example.com/elsewhere', instructions='Chop and mix.')
    technique = schemas.CookingTechniqueCreate(
        name='3:1 Vinaigrette Ratio', category='composition_and_ratio', summary='Three to one.', body='Oil to acid.', source_url=None
    )
    candidate = schemas.UrlImportCandidate(kind='both', recipe=recipe, technique=technique, technique_mention='Uses the ratio')

    with patched_assistant(AsyncMock(return_value=candidate)):
        result = await classify_url_content(URL, 'auto', 'content', MagicMock())

    assert result.recipe is not None and result.recipe.source_url == URL
    assert result.technique is not None and result.technique.source_url == URL
