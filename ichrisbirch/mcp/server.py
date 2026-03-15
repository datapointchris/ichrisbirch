"""MCP server for ichrisbirch — exposes tasks, habits, books, etc. as tools.

Reads ICHRISBIRCH_API_URL and ICHRISBIRCH_API_TOKEN from environment.
Authenticates via Bearer token (personal API key).
"""

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP('ichrisbirch')

API_URL = os.environ.get('ICHRISBIRCH_API_URL', 'https://api.docker.localhost')
API_TOKEN = os.environ.get('ICHRISBIRCH_API_TOKEN', '')


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=API_URL,
        headers={'Authorization': f'Bearer {API_TOKEN}'},
        verify=False,  # noqa: S501  # nosec B501  # dev certs are self-signed
        timeout=30,
    )


def _json_response(response: httpx.Response) -> str:
    """Return JSON string from response, or error message."""
    if response.is_success:
        if response.status_code == 204:
            return json.dumps({'status': 'success'})
        return json.dumps(response.json(), default=str)
    return json.dumps({'error': response.status_code, 'detail': response.text})


# =============================================================================
# TASKS
# =============================================================================


@mcp.tool()
def list_todo_tasks(limit: int | None = None) -> str:
    """List incomplete (todo) tasks, ordered by priority."""
    params = {}
    if limit:
        params['limit'] = limit
    with _client() as c:
        return _json_response(c.get('/tasks/todo/', params=params))


@mcp.tool()
def list_completed_tasks(start_date: str | None = None, end_date: str | None = None) -> str:
    """List completed tasks, optionally filtered by date range (ISO format)."""
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    with _client() as c:
        return _json_response(c.get('/tasks/completed/', params=params))


@mcp.tool()
def search_tasks(query: str) -> str:
    """Search tasks by name or notes."""
    with _client() as c:
        return _json_response(c.get('/tasks/search/', params={'q': query}))


@mcp.tool()
def create_task(name: str, category: str, priority: int, notes: str | None = None) -> str:
    """Create a new task.

    Categories: Automotive, Chore, Computer, Dingo, Financial, Home, Kitchen, Learn, Personal, Purchase, Research, Work.
    """
    payload: dict = {'name': name, 'category': category, 'priority': priority}
    if notes:
        payload['notes'] = notes
    with _client() as c:
        return _json_response(c.post('/tasks/', json=payload))


@mcp.tool()
def update_task(
    id: int,
    name: str | None = None,
    category: str | None = None,
    priority: int | None = None,
    notes: str | None = None,
) -> str:
    """Update an existing task by ID. Only provided fields are changed."""
    payload = {k: v for k, v in {'name': name, 'category': category, 'priority': priority, 'notes': notes}.items() if v is not None}
    with _client() as c:
        return _json_response(c.patch(f'/tasks/{id}/', json=payload))


@mcp.tool()
def complete_task(id: int) -> str:
    """Mark a task as complete."""
    with _client() as c:
        return _json_response(c.patch(f'/tasks/{id}/complete/'))


@mcp.tool()
def delete_task(id: int) -> str:
    """Delete a task by ID."""
    with _client() as c:
        return _json_response(c.delete(f'/tasks/{id}/'))


# =============================================================================
# HABITS
# =============================================================================


@mcp.tool()
def list_habits(is_current: bool | None = None) -> str:
    """List habits. Optionally filter by is_current."""
    params = {}
    if is_current is not None:
        params['is_current'] = is_current
    with _client() as c:
        return _json_response(c.get('/habits/', params=params))


@mcp.tool()
def list_habit_categories() -> str:
    """List all habit categories."""
    with _client() as c:
        return _json_response(c.get('/habits/categories/'))


@mcp.tool()
def list_completed_habits(start_date: str | None = None, end_date: str | None = None) -> str:
    """List completed habit entries, optionally filtered by date range."""
    params = {}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    with _client() as c:
        return _json_response(c.get('/habits/completed/', params=params))


@mcp.tool()
def create_habit(name: str, category_id: int, is_current: bool = True) -> str:
    """Create a new habit."""
    with _client() as c:
        return _json_response(c.post('/habits/', json={'name': name, 'category_id': category_id, 'is_current': is_current}))


@mcp.tool()
def complete_habit(name: str, category_id: int, complete_date: str) -> str:
    """Record a habit completion. complete_date in ISO format."""
    with _client() as c:
        return _json_response(c.post('/habits/completed/', json={'name': name, 'category_id': category_id, 'complete_date': complete_date}))


# =============================================================================
# EVENTS
# =============================================================================


@mcp.tool()
def list_events() -> str:
    """List all events."""
    with _client() as c:
        return _json_response(c.get('/events/'))


@mcp.tool()
def create_event(
    name: str,
    date: str,
    venue: str,
    cost: float,
    attending: bool,
    url: str | None = None,
    notes: str | None = None,
) -> str:
    """Create a new event. Date in ISO format."""
    payload: dict = {'name': name, 'date': date, 'venue': venue, 'cost': cost, 'attending': attending}
    if url:
        payload['url'] = url
    if notes:
        payload['notes'] = notes
    with _client() as c:
        return _json_response(c.post('/events/', json=payload))


@mcp.tool()
def update_event(
    id: int,
    name: str | None = None,
    date: str | None = None,
    venue: str | None = None,
    cost: float | None = None,
    attending: bool | None = None,
    url: str | None = None,
    notes: str | None = None,
) -> str:
    """Update an event by ID. Only provided fields are changed."""
    payload = {
        k: v
        for k, v in {'name': name, 'date': date, 'venue': venue, 'cost': cost, 'attending': attending, 'url': url, 'notes': notes}.items()
        if v is not None
    }
    with _client() as c:
        return _json_response(c.patch(f'/events/{id}/', json=payload))


@mcp.tool()
def delete_event(id: int) -> str:
    """Delete an event by ID."""
    with _client() as c:
        return _json_response(c.delete(f'/events/{id}/'))


# =============================================================================
# BOOKS
# =============================================================================


@mcp.tool()
def list_books(status: str | None = None) -> str:
    """List all books, optionally filtered by status (owned, to_purchase, skipped, sold, donated)."""
    params = {}
    if status:
        params['status'] = status
    with _client() as c:
        return _json_response(c.get('/books/', params=params))


@mcp.tool()
def search_books(query: str) -> str:
    """Search books by title, author, or tags."""
    with _client() as c:
        return _json_response(c.get('/books/search/', params={'q': query}))


@mcp.tool()
def create_book(
    title: str,
    author: str,
    tags: str,
    isbn: str | None = None,
    goodreads_url: str | None = None,
    rating: int | None = None,
    priority: int | None = None,
    notes: str | None = None,
    status: str | None = None,
    skip_reason: str | None = None,
    purchase_date: str | None = None,
    purchase_price: float | None = None,
    sell_date: str | None = None,
    sell_price: float | None = None,
    read_start_date: str | None = None,
    read_finish_date: str | None = None,
    abandoned: bool | None = None,
    location: str | None = None,
) -> str:
    """Create a new book entry.

    Tags is a comma-separated string (e.g. "Fiction, Classic, Adventure").
    At least one tag is required.
    Status values: owned (default), to_purchase, skipped, sold, donated.
    Date fields accept ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    """
    payload: dict = {'title': title, 'author': author, 'isbn': isbn}
    payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    optional_fields = {
        'goodreads_url': goodreads_url,
        'rating': rating,
        'priority': priority,
        'notes': notes,
        'status': status,
        'skip_reason': skip_reason,
        'purchase_date': purchase_date,
        'purchase_price': purchase_price,
        'sell_date': sell_date,
        'sell_price': sell_price,
        'read_start_date': read_start_date,
        'read_finish_date': read_finish_date,
        'abandoned': abandoned,
        'location': location,
    }
    payload.update({k: v for k, v in optional_fields.items() if v is not None})
    with _client() as c:
        return _json_response(c.post('/books/', json=payload))


@mcp.tool()
def update_book(
    id: int,
    title: str | None = None,
    author: str | None = None,
    isbn: str | None = None,
    tags: str | None = None,
    goodreads_url: str | None = None,
    rating: int | None = None,
    priority: int | None = None,
    notes: str | None = None,
    status: str | None = None,
    skip_reason: str | None = None,
    purchase_date: str | None = None,
    purchase_price: float | None = None,
    sell_date: str | None = None,
    sell_price: float | None = None,
    read_start_date: str | None = None,
    read_finish_date: str | None = None,
    abandoned: bool | None = None,
    location: str | None = None,
) -> str:
    """Update a book by ID. Only provided fields are changed.

    Tags is a comma-separated string (e.g. "Fiction, Classic, Adventure").
    Status values: owned, to_purchase, skipped, sold, donated.
    Date fields accept ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    """
    fields: dict = {
        'title': title,
        'author': author,
        'isbn': isbn,
        'goodreads_url': goodreads_url,
        'rating': rating,
        'priority': priority,
        'notes': notes,
        'status': status,
        'skip_reason': skip_reason,
        'purchase_date': purchase_date,
        'purchase_price': purchase_price,
        'sell_date': sell_date,
        'sell_price': sell_price,
        'read_start_date': read_start_date,
        'read_finish_date': read_finish_date,
        'abandoned': abandoned,
        'location': location,
    }
    payload = {k: v for k, v in fields.items() if v is not None}
    if tags is not None:
        payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    with _client() as c:
        return _json_response(c.patch(f'/books/{id}/', json=payload))


@mcp.tool()
def delete_book(id: int) -> str:
    """Delete a book by ID."""
    with _client() as c:
        return _json_response(c.delete(f'/books/{id}/'))


# =============================================================================
# ARTICLES
# =============================================================================


@mcp.tool()
def list_articles() -> str:
    """List all articles."""
    with _client() as c:
        return _json_response(c.get('/articles/'))


@mcp.tool()
def get_current_article() -> str:
    """Get the current article (the one being read)."""
    with _client() as c:
        return _json_response(c.get('/articles/current/'))


@mcp.tool()
def search_articles(query: str) -> str:
    """Search articles by title or tags."""
    with _client() as c:
        return _json_response(c.get('/articles/search/', params={'q': query}))


@mcp.tool()
def create_article(url: str, notes: str | None = None) -> str:
    """Create a new article from a URL. Auto-summarizes using AI."""
    payload: dict = {'url': url}
    if notes:
        payload['notes'] = notes
    with _client() as c:
        return _json_response(c.post('/articles/create-from-url/', json=payload))


@mcp.tool()
def bulk_import_articles(urls: str) -> str:
    """Import multiple articles from URLs (newline or comma separated). Returns a batch_id for status polling."""
    url_list = [u.strip() for u in urls.replace(',', '\n').split('\n') if u.strip()]
    if not url_list:
        return json.dumps({'error': 'No URLs provided'})
    with _client() as c:
        return _json_response(c.post('/articles/bulk-import/', json={'urls': url_list}))


@mcp.tool()
def check_bulk_import_status(batch_id: str) -> str:
    """Check status of a bulk article import batch."""
    with _client() as c:
        return _json_response(c.get(f'/articles/bulk-import/{batch_id}/'))


@mcp.tool()
def list_failed_article_imports() -> str:
    """List all permanently failed article imports."""
    with _client() as c:
        return _json_response(c.get('/articles/failed-imports/'))


@mcp.tool()
def update_article(
    id: int,
    title: str | None = None,
    url: str | None = None,
    tags: str | None = None,
    notes: str | None = None,
) -> str:
    """Update an article by ID. Only provided fields are changed.

    Tags is an optional comma-separated string (e.g. "python, databases, sql").
    """
    payload: dict[str, Any] = {k: v for k, v in {'title': title, 'url': url, 'notes': notes}.items() if v is not None}
    if tags is not None:
        payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    with _client() as c:
        return _json_response(c.patch(f'/articles/{id}/', json=payload))


# =============================================================================
# COUNTDOWNS
# =============================================================================


@mcp.tool()
def list_countdowns() -> str:
    """List all countdowns."""
    with _client() as c:
        return _json_response(c.get('/countdowns/'))


@mcp.tool()
def create_countdown(name: str, due_date: str, notes: str | None = None) -> str:
    """Create a new countdown. due_date in ISO format."""
    payload: dict = {'name': name, 'due_date': due_date}
    if notes:
        payload['notes'] = notes
    with _client() as c:
        return _json_response(c.post('/countdowns/', json=payload))


@mcp.tool()
def delete_countdown(id: int) -> str:
    """Delete a countdown by ID."""
    with _client() as c:
        return _json_response(c.delete(f'/countdowns/{id}/'))


# =============================================================================
# AUTOTASKS
# =============================================================================


@mcp.tool()
def list_autotasks() -> str:
    """List all auto-tasks (recurring task templates)."""
    with _client() as c:
        return _json_response(c.get('/autotasks/'))
