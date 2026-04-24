"""MCP server for ichrisbirch — exposes tasks, habits, books, etc. as tools.

Reads ICHRISBIRCH_API_URL and ICHRISBIRCH_API_TOKEN from environment.
Authenticates via Bearer token (personal API key).
"""

import datetime
import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

MCP_PORT = int(os.environ.get('MCP_PORT', '8000'))

mcp = FastMCP('ichrisbirch', host='0.0.0.0', port=MCP_PORT)  # nosec B104  # Docker requires binding all interfaces

API_URL = os.environ.get('ICHRISBIRCH_API_URL', 'https://api.docker.localhost')
API_TOKEN = os.environ.get('ICHRISBIRCH_API_TOKEN', '')


def _client() -> httpx.Client:
    # Plain HTTP (internal Docker network) needs no TLS verification;
    # self-signed dev certs (https://api.docker.localhost) need verify=False;
    # real HTTPS endpoints use default verification.
    if API_URL.startswith('http://'):
        verify = True  # irrelevant for plain HTTP, but httpx requires a value
    elif 'localhost' in API_URL:
        verify = False  # noqa: S501  # nosec B501  # dev certs are self-signed
    else:
        verify = True
    return httpx.Client(
        base_url=API_URL,
        headers={'Authorization': f'Bearer {API_TOKEN}'},
        verify=verify,
        timeout=30,
    )


def _json_response(response: httpx.Response) -> str:
    """Return JSON string from response, or error message."""
    if response.is_success:
        if response.status_code == 204:
            return json.dumps({'status': 'success'})
        return json.dumps(response.json(), default=str)
    return json.dumps({'error': response.status_code, 'detail': response.text})


def _summarize(json_str: str, fields: list[str]) -> str:
    """Filter a JSON response to include only the specified fields.

    Works on both single objects and lists. Passes through error responses unchanged.
    """
    data = json.loads(json_str)
    if isinstance(data, dict) and 'error' in data:
        return json_str
    if isinstance(data, list):
        return json.dumps([{k: v for k, v in item.items() if k in fields} for item in data], default=str)
    return json.dumps({k: v for k, v in data.items() if k in fields}, default=str)


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
    null_fields: str | None = None,
) -> str:
    """Update an existing task by ID. Only provided fields are changed.

    To set a field to null, include it in null_fields (comma-separated).
    Example: null_fields="notes" sets notes to null.
    """
    fields = {'name': name, 'category': category, 'priority': priority, 'notes': notes}
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}
    if null_fields:
        for field in null_fields.split(','):
            payload[field.strip()] = None
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
def update_habit(
    id: int,
    name: str | None = None,
    category_id: int | None = None,
    is_current: bool | None = None,
) -> str:
    """Update a habit by ID. Only provided fields are changed."""
    fields = {'name': name, 'category_id': category_id, 'is_current': is_current}
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}
    with _client() as c:
        return _json_response(c.patch(f'/habits/{id}/', json=payload))


@mcp.tool()
def delete_habit(id: int) -> str:
    """Delete a habit by ID."""
    with _client() as c:
        return _json_response(c.delete(f'/habits/{id}/'))


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
    null_fields: str | None = None,
) -> str:
    """Update an event by ID. Only provided fields are changed.

    To set a field to null, include it in null_fields (comma-separated).
    Example: null_fields="url,notes" sets both to null.
    """
    payload: dict[str, Any] = {
        k: v
        for k, v in {'name': name, 'date': date, 'venue': venue, 'cost': cost, 'attending': attending, 'url': url, 'notes': notes}.items()
        if v is not None
    }
    if null_fields:
        for field in null_fields.split(','):
            payload[field.strip()] = None
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


BOOK_SUMMARY_FIELDS = ['id', 'title', 'author', 'tags', 'notes', 'progress', 'rating']


@mcp.tool()
def get_book(id: int) -> str:
    """Get full details for a single book by ID."""
    with _client() as c:
        return _json_response(c.get(f'/books/{id}/'))


@mcp.tool()
def list_books(ownership: str | None = None) -> str:
    """List all books (summary: id, title, author, tags, notes, progress, rating).

    Use get_book(id) for full details on a specific book.
    Optionally filter by ownership: owned, to_purchase, rejected, sold, donated.
    """
    params = {}
    if ownership:
        params['ownership'] = ownership
    with _client() as c:
        return _summarize(_json_response(c.get('/books/', params=params)), BOOK_SUMMARY_FIELDS)


@mcp.tool()
def search_books(query: str) -> str:
    """Search books by title, author, or tags (summary: id, title, author, tags, notes, progress, rating).

    Use get_book(id) for full details on a specific book.
    """
    with _client() as c:
        return _summarize(_json_response(c.get('/books/search/', params={'q': query})), BOOK_SUMMARY_FIELDS)


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
    review: str | None = None,
    ownership: str | None = None,
    progress: str | None = None,
    reject_reason: str | None = None,
    purchase_date: str | None = None,
    purchase_price: float | None = None,
    sell_date: str | None = None,
    sell_price: float | None = None,
    read_start_date: str | None = None,
    read_finish_date: str | None = None,
    location: str | None = None,
) -> str:
    """Create a new book entry.

    Tags is a comma-separated string (e.g. "Fiction, Classic, Adventure").
    At least one tag is required.
    Ownership values: owned (default), to_purchase, rejected, sold, donated.
    Progress values: unread (default), reading, read, abandoned.
    Date fields accept ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    """
    payload: dict = {'title': title, 'author': author, 'isbn': isbn}
    payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    optional_fields = {
        'goodreads_url': goodreads_url,
        'rating': rating,
        'priority': priority,
        'notes': notes,
        'review': review,
        'ownership': ownership,
        'progress': progress,
        'reject_reason': reject_reason,
        'purchase_date': purchase_date,
        'purchase_price': purchase_price,
        'sell_date': sell_date,
        'sell_price': sell_price,
        'read_start_date': read_start_date,
        'read_finish_date': read_finish_date,
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
    review: str | None = None,
    ownership: str | None = None,
    progress: str | None = None,
    reject_reason: str | None = None,
    purchase_date: str | None = None,
    purchase_price: float | None = None,
    sell_date: str | None = None,
    sell_price: float | None = None,
    read_start_date: str | None = None,
    read_finish_date: str | None = None,
    location: str | None = None,
    null_fields: str | None = None,
) -> str:
    """Update a book by ID. Only provided fields are changed.

    Tags is a comma-separated string (e.g. "Fiction, Classic, Adventure").
    Ownership values: owned, to_purchase, rejected, sold, donated.
    Progress values: unread, reading, read, abandoned.
    Date fields accept ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    To set a field to null, include it in null_fields (comma-separated).
    Example: null_fields="priority,notes" sets both to null.
    """
    fields: dict = {
        'title': title,
        'author': author,
        'isbn': isbn,
        'goodreads_url': goodreads_url,
        'rating': rating,
        'priority': priority,
        'notes': notes,
        'review': review,
        'ownership': ownership,
        'progress': progress,
        'reject_reason': reject_reason,
        'purchase_date': purchase_date,
        'purchase_price': purchase_price,
        'sell_date': sell_date,
        'sell_price': sell_price,
        'read_start_date': read_start_date,
        'read_finish_date': read_finish_date,
        'location': location,
    }
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}
    if tags is not None:
        payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    if null_fields:
        for field in null_fields.split(','):
            payload[field.strip()] = None
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

ARTICLE_SUMMARY_FIELDS = ['id', 'title', 'url', 'tags', 'summary']


@mcp.tool()
def list_articles(
    favorites: bool | None = None,
    archived: bool | None = None,
    unread: bool | None = None,
) -> str:
    """List articles (summary: id, title, url, tags, summary).

    favorites=True: only favorites due for re-read. archived=True/False: filter by archived state.
    unread=True: never-read articles only.
    """
    params: dict[str, Any] = {}
    if favorites is not None:
        params['favorites'] = favorites
    if archived is not None:
        params['archived'] = archived
    if unread is not None:
        params['unread'] = unread
    with _client() as c:
        return _summarize(_json_response(c.get('/articles/', params=params)), ARTICLE_SUMMARY_FIELDS)


@mcp.tool()
def get_current_article() -> str:
    """Get the current article (the one being read). Returns full detail."""
    with _client() as c:
        return _json_response(c.get('/articles/current/'))


@mcp.tool()
def search_articles(query: str) -> str:
    """Search articles by title or tags (summary: id, title, url, tags, summary)."""
    with _client() as c:
        return _summarize(_json_response(c.get('/articles/search/', params={'q': query})), ARTICLE_SUMMARY_FIELDS)


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
    tags: str | None = None,
    summary: str | None = None,
    notes: str | None = None,
    is_favorite: bool | None = None,
    is_current: bool | None = None,
    is_archived: bool | None = None,
    review_days: int | None = None,
    last_read_date: str | None = None,
    read_count: int | None = None,
    null_fields: str | None = None,
) -> str:
    """Update an article by ID. Only provided fields are changed.

    Tags is an optional comma-separated string (e.g. "python, databases, sql").
    last_read_date accepts ISO format (YYYY-MM-DDTHH:MM:SS).
    To set a field to null, include it in null_fields (comma-separated).
    Example: null_fields="notes,review_days" sets both to null.
    """
    scalar_fields = {
        'title': title,
        'summary': summary,
        'notes': notes,
        'is_favorite': is_favorite,
        'is_current': is_current,
        'is_archived': is_archived,
        'review_days': review_days,
        'last_read_date': last_read_date,
        'read_count': read_count,
    }
    payload: dict[str, Any] = {k: v for k, v in scalar_fields.items() if v is not None}
    if tags is not None:
        payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    if null_fields:
        for field in null_fields.split(','):
            payload[field.strip()] = None
    with _client() as c:
        return _json_response(c.patch(f'/articles/{id}/', json=payload))


@mcp.tool()
def mark_article_read(id: int) -> str:
    """Mark an article as read: archives it, increments read_count, sets last_read_date to now."""
    with _client() as c:
        current = c.get(f'/articles/{id}/')
        if not current.is_success:
            return _json_response(current)
        article = current.json()
        payload = {
            'is_archived': True,
            'read_count': article['read_count'] + 1,
            'last_read_date': datetime.datetime.now(datetime.UTC).isoformat(),
        }
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
def update_countdown(
    id: int,
    name: str | None = None,
    due_date: str | None = None,
    notes: str | None = None,
    null_fields: str | None = None,
) -> str:
    """Update a countdown by ID. Only provided fields are changed.

    due_date in ISO format (YYYY-MM-DD).
    To set notes to null, pass null_fields="notes".
    """
    fields = {'name': name, 'due_date': due_date, 'notes': notes}
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}
    if null_fields:
        for field in null_fields.split(','):
            payload[field.strip()] = None
    with _client() as c:
        return _json_response(c.patch(f'/countdowns/{id}/', json=payload))


@mcp.tool()
def delete_countdown(id: int) -> str:
    """Delete a countdown by ID."""
    with _client() as c:
        return _json_response(c.delete(f'/countdowns/{id}/'))


# =============================================================================
# PROJECTS
# =============================================================================

PROJECT_ITEM_SUMMARY_FIELDS = ['id', 'title', 'notes', 'completed', 'archived']


@mcp.tool()
def list_projects() -> str:
    """List all projects with item counts, ordered by position."""
    with _client() as c:
        return _json_response(c.get('/projects/'))


@mcp.tool()
def create_project(name: str, description: str | None = None) -> str:
    """Create a new project."""
    payload: dict[str, Any] = {'name': name}
    if description:
        payload['description'] = description
    with _client() as c:
        return _json_response(c.post('/projects/', json=payload))


@mcp.tool()
def update_project(id: str, name: str | None = None, description: str | None = None, position: int | None = None) -> str:
    """Update a project by UUID. Only provided fields are changed."""
    payload: dict[str, Any] = {k: v for k, v in {'name': name, 'description': description, 'position': position}.items() if v is not None}
    with _client() as c:
        return _json_response(c.patch(f'/projects/{id}/', json=payload))


@mcp.tool()
def delete_project(id: str) -> str:
    """Delete a project by UUID. Fails if items belong only to this project."""
    with _client() as c:
        return _json_response(c.delete(f'/projects/{id}/'))


@mcp.tool()
def list_project_items(project_id: str, archived: bool = False) -> str:
    """List items in a project (summary: id, title, notes, completed, archived).

    Set archived=True to include archived items.
    """
    params: dict[str, Any] = {}
    if archived:
        params['archived'] = True
    with _client() as c:
        return _summarize(_json_response(c.get(f'/projects/{project_id}/items/', params=params)), PROJECT_ITEM_SUMMARY_FIELDS)


@mcp.tool()
def get_project_item(id: str) -> str:
    """Get full details for a project item including its projects and dependency_ids."""
    with _client() as c:
        return _json_response(c.get(f'/project-items/{id}/'))


@mcp.tool()
def create_project_item(title: str, project_ids: str, notes: str | None = None) -> str:
    """Create a new project item.

    project_ids is a comma-separated list of project UUIDs (e.g. "019d3ce0-...,019d3ce1-...").
    At least one project ID is required.
    """
    ids = [x.strip() for x in project_ids.split(',') if x.strip()]
    payload: dict[str, Any] = {'title': title, 'project_ids': ids}
    if notes:
        payload['notes'] = notes
    with _client() as c:
        return _json_response(c.post('/project-items/', json=payload))


@mcp.tool()
def update_project_item(
    id: str,
    title: str | None = None,
    notes: str | None = None,
    completed: bool | None = None,
    archived: bool | None = None,
    null_fields: str | None = None,
) -> str:
    """Update a project item by UUID. Only provided fields are changed.

    To set a field to null, include it in null_fields (comma-separated).
    """
    fields = {'title': title, 'notes': notes, 'completed': completed, 'archived': archived}
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}
    if null_fields:
        for field in null_fields.split(','):
            payload[field.strip()] = None
    with _client() as c:
        return _json_response(c.patch(f'/project-items/{id}/', json=payload))


@mcp.tool()
def delete_project_item(id: str) -> str:
    """Delete a project item by UUID."""
    with _client() as c:
        return _json_response(c.delete(f'/project-items/{id}/'))


@mcp.tool()
def search_project_items(query: str) -> str:
    """Search project items by title or notes (summary: id, title, notes, completed, archived)."""
    with _client() as c:
        return _summarize(_json_response(c.get('/project-items/search/', params={'q': query})), PROJECT_ITEM_SUMMARY_FIELDS)


@mcp.tool()
def add_project_item_dependency(item_id: str, depends_on_id: str) -> str:
    """Add a dependency: item_id will be blocked by depends_on_id.

    Fails with 409 if this would create a cycle.
    """
    with _client() as c:
        return _json_response(c.post(f'/project-items/{item_id}/dependencies/', json={'depends_on_id': depends_on_id}))


@mcp.tool()
def remove_project_item_dependency(item_id: str, depends_on_id: str) -> str:
    """Remove a dependency between two project items."""
    with _client() as c:
        return _json_response(c.delete(f'/project-items/{item_id}/dependencies/{depends_on_id}/'))


@mcp.tool()
def get_project_item_blockers(item_id: str) -> str:
    """Get incomplete items that block this item."""
    with _client() as c:
        return _summarize(_json_response(c.get(f'/project-items/{item_id}/blockers/')), PROJECT_ITEM_SUMMARY_FIELDS)


@mcp.tool()
def add_project_item_to_project(item_id: str, project_id: str) -> str:
    """Add a project item to an additional project (multi-project membership)."""
    with _client() as c:
        return _json_response(c.post(f'/project-items/{item_id}/projects/', json={'project_id': project_id}))


@mcp.tool()
def remove_project_item_from_project(item_id: str, project_id: str) -> str:
    """Remove a project item from a project. Fails if it's the item's last project."""
    with _client() as c:
        return _json_response(c.delete(f'/project-items/{item_id}/projects/{project_id}/'))


# =============================================================================
# PROJECT ITEM TASKS
# =============================================================================


@mcp.tool()
def list_project_item_tasks(item_id: str) -> str:
    """List all tasks (sub-tasks) for a project item, ordered by position."""
    with _client() as c:
        return _json_response(c.get(f'/project-items/{item_id}/tasks/'))


@mcp.tool()
def create_project_item_task(item_id: str, title: str) -> str:
    """Create a new task (sub-task) on a project item."""
    with _client() as c:
        return _json_response(c.post(f'/project-items/{item_id}/tasks/', json={'title': title}))


@mcp.tool()
def update_project_item_task(
    item_id: str, task_id: str, title: str | None = None, completed: bool | None = None, position: int | None = None
) -> str:
    """Update a project item task. Only provided fields are changed."""
    fields = {'title': title, 'completed': completed, 'position': position}
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}
    with _client() as c:
        return _json_response(c.patch(f'/project-items/{item_id}/tasks/{task_id}/', json=payload))


@mcp.tool()
def delete_project_item_task(item_id: str, task_id: str) -> str:
    """Delete a project item task."""
    with _client() as c:
        return _json_response(c.delete(f'/project-items/{item_id}/tasks/{task_id}/'))


@mcp.tool()
def complete_project_item_task(item_id: str, task_id: str) -> str:
    """Mark a project item task as complete."""
    with _client() as c:
        return _json_response(c.patch(f'/project-items/{item_id}/tasks/{task_id}/', json={'completed': True}))


# =============================================================================
# AUTOTASKS
# =============================================================================


@mcp.tool()
def list_autotasks() -> str:
    """List all auto-tasks (recurring task templates)."""
    with _client() as c:
        return _json_response(c.get('/autotasks/'))


# =============================================================================
# RECIPES
# =============================================================================

RECIPE_SUMMARY_FIELDS = [
    'id',
    'name',
    'cuisine',
    'meal_type',
    'difficulty',
    'total_time_minutes',
    'servings',
    'rating',
    'times_made',
]


@mcp.tool()
def list_recipes(
    cuisine: str | None = None,
    meal_type: str | None = None,
    difficulty: str | None = None,
    rating_min: int | None = None,
    max_total_time: int | None = None,
) -> str:
    """List recipes with summary fields.

    Filters (all optional):
    - cuisine: american, italian, mexican, asian, indian, mediterranean, french, other
    - meal_type: breakfast, lunch, dinner, snack, dessert, side, sauce, drink
    - difficulty: easy, medium, hard
    - rating_min: 1-5
    - max_total_time: minutes

    Use get_recipe(id) for full detail including ingredients and instructions.
    """
    params: dict[str, Any] = {}
    if cuisine:
        params['cuisine'] = cuisine
    if meal_type:
        params['meal_type'] = meal_type
    if difficulty:
        params['difficulty'] = difficulty
    if rating_min is not None:
        params['rating_min'] = rating_min
    if max_total_time is not None:
        params['max_total_time'] = max_total_time
    with _client() as c:
        return _summarize(_json_response(c.get('/recipes/', params=params)), RECIPE_SUMMARY_FIELDS)


@mcp.tool()
def get_recipe(id: int, servings: int | None = None) -> str:
    """Get full details for a recipe by ID, including ingredients and instructions.

    Pass `servings` to receive scaled quantities on each ingredient (scaled_quantity field).
    """
    params: dict[str, Any] = {}
    if servings is not None:
        params['servings'] = servings
    with _client() as c:
        return _json_response(c.get(f'/recipes/{id}/', params=params))


@mcp.tool()
def search_recipes(query: str) -> str:
    """Search recipes by name, tags, or instruction text.

    Pass comma-separated phrases or whitespace-separated keywords.
    Returns summary fields; use get_recipe(id) for full detail.
    """
    with _client() as c:
        return _summarize(_json_response(c.get('/recipes/search/', params={'q': query})), RECIPE_SUMMARY_FIELDS)


@mcp.tool()
def search_recipes_by_ingredients(have: str, match: str = 'any') -> str:
    """Find recipes whose ingredients match the provided list.

    `have` is comma-separated (e.g. "chicken, lemon, garlic").
    `match='any'` — rank by coverage (how many matched), descending.
    `match='all'` — only return recipes that contain every listed ingredient.

    Returns list of {recipe, coverage, total_ingredients}.
    """
    with _client() as c:
        return _json_response(c.get('/recipes/search-by-ingredients/', params={'have': have, 'match': match}))


@mcp.tool()
def create_recipe(
    name: str,
    instructions: str,
    ingredients_json: str,
    description: str | None = None,
    source_url: str | None = None,
    source_name: str | None = None,
    prep_time_minutes: int | None = None,
    cook_time_minutes: int | None = None,
    total_time_minutes: int | None = None,
    servings: int = 4,
    difficulty: str | None = None,
    cuisine: str | None = None,
    meal_type: str | None = None,
    tags: str | None = None,
    notes: str | None = None,
    rating: int | None = None,
) -> str:
    """Create a new recipe with structured ingredients.

    `ingredients_json` is a JSON array of objects, each with fields:
      {"quantity": number|null, "unit": string|null, "item": string,
       "prep_note": string|null, "is_optional": bool, "ingredient_group": string|null}

    Example: '[{"quantity": 1, "unit": "cup", "item": "flour", "prep_note": null, "is_optional": false, "ingredient_group": null}]'

    Valid units: cup, tbsp, tsp, oz, fl_oz, lb, g, kg, ml, l, pinch, dash, clove, slice, can, package, piece, whole, to_taste.
    `tags` is comma-separated.
    """
    try:
        raw_ingredients = json.loads(ingredients_json)
    except json.JSONDecodeError as e:
        return json.dumps({'error': 'invalid_ingredients_json', 'detail': str(e)})
    ingredients = [
        {
            'position': ing.get('position', idx),
            'quantity': ing.get('quantity'),
            'unit': ing.get('unit'),
            'item': ing['item'],
            'prep_note': ing.get('prep_note'),
            'is_optional': ing.get('is_optional', False),
            'ingredient_group': ing.get('ingredient_group'),
        }
        for idx, ing in enumerate(raw_ingredients)
    ]
    payload: dict[str, Any] = {
        'name': name,
        'instructions': instructions,
        'servings': servings,
        'ingredients': ingredients,
    }
    optional_fields = {
        'description': description,
        'source_url': source_url,
        'source_name': source_name,
        'prep_time_minutes': prep_time_minutes,
        'cook_time_minutes': cook_time_minutes,
        'total_time_minutes': total_time_minutes,
        'difficulty': difficulty,
        'cuisine': cuisine,
        'meal_type': meal_type,
        'notes': notes,
        'rating': rating,
    }
    payload.update({k: v for k, v in optional_fields.items() if v is not None})
    if tags:
        payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    with _client() as c:
        return _json_response(c.post('/recipes/', json=payload))


@mcp.tool()
def update_recipe(
    id: int,
    name: str | None = None,
    description: str | None = None,
    instructions: str | None = None,
    source_url: str | None = None,
    source_name: str | None = None,
    prep_time_minutes: int | None = None,
    cook_time_minutes: int | None = None,
    total_time_minutes: int | None = None,
    servings: int | None = None,
    difficulty: str | None = None,
    cuisine: str | None = None,
    meal_type: str | None = None,
    tags: str | None = None,
    notes: str | None = None,
    rating: int | None = None,
    ingredients_json: str | None = None,
    null_fields: str | None = None,
) -> str:
    """Update a recipe by ID. Only provided fields are changed.

    If `ingredients_json` is provided, it REPLACES the entire ingredient list (replace-all semantics).
    `tags` is comma-separated. `null_fields` is comma-separated list of fields to set to null.
    """
    fields = {
        'name': name,
        'description': description,
        'instructions': instructions,
        'source_url': source_url,
        'source_name': source_name,
        'prep_time_minutes': prep_time_minutes,
        'cook_time_minutes': cook_time_minutes,
        'total_time_minutes': total_time_minutes,
        'servings': servings,
        'difficulty': difficulty,
        'cuisine': cuisine,
        'meal_type': meal_type,
        'notes': notes,
        'rating': rating,
    }
    payload: dict[str, Any] = {k: v for k, v in fields.items() if v is not None}
    if tags is not None:
        payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    if ingredients_json is not None:
        try:
            raw = json.loads(ingredients_json)
        except json.JSONDecodeError as e:
            return json.dumps({'error': 'invalid_ingredients_json', 'detail': str(e)})
        payload['ingredients'] = [
            {
                'position': ing.get('position', idx),
                'quantity': ing.get('quantity'),
                'unit': ing.get('unit'),
                'item': ing['item'],
                'prep_note': ing.get('prep_note'),
                'is_optional': ing.get('is_optional', False),
                'ingredient_group': ing.get('ingredient_group'),
            }
            for idx, ing in enumerate(raw)
        ]
    if null_fields:
        for field in null_fields.split(','):
            payload[field.strip()] = None
    with _client() as c:
        return _json_response(c.patch(f'/recipes/{id}/', json=payload))


@mcp.tool()
def delete_recipe(id: int) -> str:
    """Delete a recipe by ID."""
    with _client() as c:
        return _json_response(c.delete(f'/recipes/{id}/'))


@mcp.tool()
def mark_recipe_made(id: int) -> str:
    """Increment the times_made counter and set last_made_date to now."""
    with _client() as c:
        return _json_response(c.post(f'/recipes/{id}/mark-made/'))


@mcp.tool()
def ai_suggest_recipes(have: str, want: str | None = None, count: int = 3) -> str:
    """Ask Claude (with web search) to find recipes matching available ingredients.

    `have` is comma-separated ingredients on hand.
    `want` is a free-form description of the kind of dish (optional).
    `count` is how many suggestions to return (default 3).

    Returns candidates WITHOUT saving — use ai_save_recipe(candidate_json) per result to persist.
    This call may take 30-60 seconds due to the web search.
    """
    payload = {
        'have': [s.strip() for s in have.split(',') if s.strip()],
        'want': want,
        'count': count,
    }
    with _client() as c:
        return _json_response(c.post('/recipes/ai-suggest/', json=payload))


@mcp.tool()
def ai_save_recipe(candidate_json: str) -> str:
    """Save an AI-generated candidate to the recipes table.

    Pass a JSON object matching the RecipeCandidate schema (as returned from ai_suggest_recipes).
    """
    try:
        candidate = json.loads(candidate_json)
    except json.JSONDecodeError as e:
        return json.dumps({'error': 'invalid_candidate_json', 'detail': str(e)})
    with _client() as c:
        return _json_response(c.post('/recipes/ai-save/', json=candidate))


# =============================================================================
# COOKING TECHNIQUES
# =============================================================================
# Reusable cooking patterns inside the Recipes domain — served under
# /recipes/cooking-techniques/. Categories: heat_application, flavor_development,
# emulsion_and_texture, preservation_and_pre_treatment, seasoning_and_finishing,
# dough_and_batter, knife_work_and_prep, composition_and_ratio, equipment_technique.

COOKING_TECHNIQUES_ENDPOINT = '/recipes/cooking-techniques/'
COOKING_TECHNIQUE_SUMMARY_FIELDS = ['id', 'name', 'slug', 'category', 'summary', 'tags', 'rating']


@mcp.tool()
def list_cooking_techniques(category: str | None = None, rating_min: int | None = None) -> str:
    """List cooking techniques with summary fields (id, name, slug, category, summary, tags, rating).

    Filters (all optional):
    - category: one of the 9 fixed categories (see module docstring)
    - rating_min: 1-5

    Use get_cooking_technique(id) for the full body, why_it_works, and common_pitfalls.
    """
    params: dict[str, Any] = {}
    if category:
        params['category'] = category
    if rating_min is not None:
        params['rating_min'] = rating_min
    with _client() as c:
        return _summarize(_json_response(c.get(COOKING_TECHNIQUES_ENDPOINT, params=params)), COOKING_TECHNIQUE_SUMMARY_FIELDS)


@mcp.tool()
def get_cooking_technique(id: int) -> str:
    """Get the full cooking technique record by ID — includes body (markdown), why_it_works, and common_pitfalls."""
    with _client() as c:
        return _json_response(c.get(f'{COOKING_TECHNIQUES_ENDPOINT}{id}/'))


@mcp.tool()
def get_cooking_technique_by_slug(slug: str) -> str:
    """Get a cooking technique by URL-safe slug (e.g. 'vinaigrette-ratio-3-1')."""
    with _client() as c:
        return _json_response(c.get(f'{COOKING_TECHNIQUES_ENDPOINT}slug/{slug}/'))


@mcp.tool()
def search_cooking_techniques(query: str) -> str:
    """Search cooking techniques by name, summary, body, or tags.

    Pass comma-separated phrases or whitespace-separated keywords.
    Returns summary fields; use get_cooking_technique(id) for full detail.
    """
    with _client() as c:
        return _summarize(
            _json_response(c.get(f'{COOKING_TECHNIQUES_ENDPOINT}search/', params={'q': query})),
            COOKING_TECHNIQUE_SUMMARY_FIELDS,
        )


@mcp.tool()
def list_cooking_technique_categories() -> str:
    """List all 9 cooking technique categories with counts.

    Includes zero-count categories so every bucket is visible.
    Returns [{"name": str, "count": int}, ...].
    """
    with _client() as c:
        return _json_response(c.get(f'{COOKING_TECHNIQUES_ENDPOINT}categories/'))


@mcp.tool()
def create_cooking_technique(
    name: str,
    category: str,
    summary: str,
    body: str,
    why_it_works: str | None = None,
    common_pitfalls: str | None = None,
    source_url: str | None = None,
    source_name: str | None = None,
    tags: str | None = None,
    rating: int | None = None,
) -> str:
    """Create a new cooking technique.

    `category` must be one of: heat_application, flavor_development, emulsion_and_texture,
    preservation_and_pre_treatment, seasoning_and_finishing, dough_and_batter,
    knife_work_and_prep, composition_and_ratio, equipment_technique.

    `body` is long-form markdown — the full write-up.
    `summary` is a one-paragraph TL;DR.
    `tags` is comma-separated.
    `rating` is 1-5.

    Slug is generated server-side from `name` and cannot be set.
    """
    payload: dict[str, Any] = {
        'name': name,
        'category': category,
        'summary': summary,
        'body': body,
    }
    optional_fields = {
        'why_it_works': why_it_works,
        'common_pitfalls': common_pitfalls,
        'source_url': source_url,
        'source_name': source_name,
        'rating': rating,
    }
    payload.update({k: v for k, v in optional_fields.items() if v is not None})
    if tags:
        payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    with _client() as c:
        return _json_response(c.post(COOKING_TECHNIQUES_ENDPOINT, json=payload))


@mcp.tool()
def update_cooking_technique(
    id: int,
    name: str | None = None,
    category: str | None = None,
    summary: str | None = None,
    body: str | None = None,
    why_it_works: str | None = None,
    common_pitfalls: str | None = None,
    source_url: str | None = None,
    source_name: str | None = None,
    tags: str | None = None,
    rating: int | None = None,
    null_fields: str | None = None,
) -> str:
    """Update a cooking technique by ID. Only provided fields are changed.

    Slug is NEVER updated — renaming preserves the deep link.

    `null_fields` is a comma-separated list of field names to explicitly set to NULL
    (e.g. null_fields="why_it_works,common_pitfalls").
    """
    payload: dict[str, Any] = {}
    candidates = {
        'name': name,
        'category': category,
        'summary': summary,
        'body': body,
        'why_it_works': why_it_works,
        'common_pitfalls': common_pitfalls,
        'source_url': source_url,
        'source_name': source_name,
        'rating': rating,
    }
    payload.update({k: v for k, v in candidates.items() if v is not None})
    if tags is not None:
        payload['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
    if null_fields:
        for field in null_fields.split(','):
            payload[field.strip()] = None
    with _client() as c:
        return _json_response(c.patch(f'{COOKING_TECHNIQUES_ENDPOINT}{id}/', json=payload))


@mcp.tool()
def delete_cooking_technique(id: int) -> str:
    """Delete a cooking technique by ID."""
    with _client() as c:
        return _json_response(c.delete(f'{COOKING_TECHNIQUES_ENDPOINT}{id}/'))
