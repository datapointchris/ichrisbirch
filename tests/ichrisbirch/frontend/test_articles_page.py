import pytest
from playwright.sync_api import Page
from playwright.sync_api import expect
from sqlalchemy import delete
from sqlalchemy import select

from ichrisbirch import models
from tests.factories import ArticleFactory
from tests.factories import clear_factory_session
from tests.factories import set_factory_session
from tests.ichrisbirch.frontend.fixtures import FRONTEND_BASE_URL
from tests.ichrisbirch.frontend.fixtures import login_regular_user
from tests.utils.database import create_session
from tests.utils.database import test_settings


@pytest.fixture(autouse=True)
def setup_test_articles(insert_users_for_login):
    """Create test articles using factories for this test module."""
    with create_session(test_settings) as session:
        set_factory_session(session)
        ArticleFactory(
            title='Current Article',
            url='https://example.com/current',
            tags=['python', 'testing'],
            summary='An article about testing',
            is_current=True,
            is_favorite=False,
            is_archived=False,
            read_count=0,
        )
        ArticleFactory(
            title='Favorite Article',
            url='https://example.com/favorite',
            tags=['design', 'ux'],
            summary='An article about design',
            is_current=False,
            is_favorite=True,
            is_archived=False,
            read_count=2,
        )
        ArticleFactory(
            title='Archived Article',
            url='https://example.com/archived',
            tags=['devops'],
            summary='An article about devops',
            is_current=False,
            is_favorite=False,
            is_archived=True,
            read_count=1,
        )
        session.commit()
        clear_factory_session()

    yield

    with create_session(test_settings) as session:
        session.execute(delete(models.Article))
        session.commit()


@pytest.fixture(autouse=True)
def login_homepage(setup_test_articles, page: Page):
    login_regular_user(page)
    page.goto(f'{FRONTEND_BASE_URL}/articles/')


def _get_article_from_db(title: str) -> models.Article:
    """Find an article by title via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Article).where(models.Article.title == title)).scalar_one()


def _get_article_by_id_from_db(article_id: int) -> models.Article:
    """Get an article by ID via direct DB query."""
    with create_session(test_settings) as session:
        return session.execute(select(models.Article).where(models.Article.id == article_id)).scalar_one()


def _article_exists_in_db(article_id: int) -> bool:
    """Check if an article exists in DB."""
    with create_session(test_settings) as session:
        result = session.execute(select(models.Article).where(models.Article.id == article_id)).scalar_one_or_none()
        return result is not None


def test_articles_index(page: Page):
    expect(page).to_have_title('Current Article')
    expect(page.locator('h2 a')).to_have_text('Current Article')


def test_articles_all(page: Page):
    page.goto(f'{FRONTEND_BASE_URL}/articles/all/')
    expect(page).to_have_title('Articles')
    # All 3 articles should be visible
    expect(page.locator('.grid__item h2')).to_have_count(3)


def test_add_article(page: Page):
    """Fill the add form in a real browser, submit, verify in DB."""
    page.goto(f'{FRONTEND_BASE_URL}/articles/add/')
    expect(page).to_have_title('Articles')

    # Scope to the add form to avoid conflicts with other elements in the base template
    form = page.locator('form.add-item-form')
    form.locator('#url').fill('https://example.com/new-playwright-article')
    form.locator('#title').fill('Playwright Test Article')
    form.locator('#tags').fill('playwright, testing, integration')
    form.locator('#summary').fill('Created by Playwright test')
    form.locator('#notes').fill('Some notes')
    form.locator('button[value="add"]').click()

    article = _get_article_from_db('Playwright Test Article')
    assert article.url == 'https://example.com/new-playwright-article'
    assert article.tags == ['playwright', 'testing', 'integration']
    assert article.summary == 'Created by Playwright test'
    assert article.notes == 'Some notes'
    assert article.is_archived is not True
    assert article.is_favorite is not True


def test_article_status_transitions(page: Page):
    """Click through status transitions on the article card, verify each persists.

    Tests the real user flow: the index page shows one article with action buttons.
    Each button click posts to /crud/ and redirects back. We verify in the DB that
    each state change is correct and that previous state survives.
    """
    article = _get_article_from_db('Current Article')
    article_id = article.id

    # Index page should show the current article with action buttons
    expect(page.locator('h2 a')).to_have_text('Current Article')

    # === Step 1: Make favorite ===
    page.locator('button[value="make_favorite"]').click()

    result = _get_article_by_id_from_db(article_id)
    assert result.is_favorite is True
    assert result.is_current is True, 'Current status should survive'

    # Page should now show "Unfavorite" button instead
    expect(page.locator('button[value="unfavorite"]')).to_be_visible()

    # === Step 2: Mark as read (archives + sets current=False + increments read_count) ===
    page.locator('button[value="mark_read"]').click()

    result = _get_article_by_id_from_db(article_id)
    assert result.read_count >= 1, 'Read count should be incremented'
    assert result.is_archived is True, 'Mark read should archive'
    assert result.is_current is False, 'Mark read should remove current status'
    assert result.is_favorite is True, 'Favorite should survive mark_read'

    # After mark_read, the article is no longer current, so the index page
    # will show a different article or "No articles". Navigate to all articles
    # to find it and continue testing.
    page.goto(f'{FRONTEND_BASE_URL}/articles/all/')

    # Find the form for our specific article by its hidden id input
    article_form = page.locator(f'form:has(input[name="id"][value="{article_id}"])')

    # === Step 3: Unarchive ===
    article_form.locator('button[value="unarchive"]').click()

    result = _get_article_by_id_from_db(article_id)
    assert result.is_archived is not True, 'Should be unarchived'
    assert result.is_favorite is True, 'Favorite should survive unarchive'
    assert result.read_count >= 1, 'Read count should survive unarchive'

    # === Step 4: Unfavorite ===
    page.goto(f'{FRONTEND_BASE_URL}/articles/all/')
    article_form = page.locator(f'form:has(input[name="id"][value="{article_id}"])')
    article_form.locator('button[value="unfavorite"]').click()

    result = _get_article_by_id_from_db(article_id)
    assert result.is_favorite is not True, 'Should be unfavorited'
    assert result.read_count >= 1, 'Read count should survive unfavorite'


def test_search_articles(page: Page):
    """Search for an article and verify results appear."""
    page.goto(f'{FRONTEND_BASE_URL}/articles/search/')

    page.locator('input[name="search_text"]').fill('testing')
    page.locator('button[value="search"]').click()

    # Should find the "Current Article" which has 'testing' tag — scope to search results
    expect(page.locator('.articles-search-results__item', has_text='Current Article')).to_be_visible()


def test_delete_article(page: Page):
    """Delete an article via button click, verify it's gone from DB."""
    article = _get_article_from_db('Archived Article')
    article_id = article.id

    page.goto(f'{FRONTEND_BASE_URL}/articles/all/')

    # Target the delete button in the specific article's form
    article_form = page.locator(f'form:has(input[name="id"][value="{article_id}"])')
    article_form.locator('button[value="delete"]').click()

    assert not _article_exists_in_db(article_id), 'Article should be deleted'
