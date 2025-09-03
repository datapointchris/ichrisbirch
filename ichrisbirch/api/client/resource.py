from typing import TYPE_CHECKING
from typing import Any
from typing import TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from .session import APISession

T = TypeVar('T', bound=BaseModel)


class ResourceClient[T]:
    """Generic resource client for any API endpoint."""

    def __init__(self, session: 'APISession', resource_name: str, model_class: type[T]):
        self.session = session
        self.resource_name = resource_name
        self.model_class = model_class
        self.base_endpoint = f'/{resource_name}'

    def get(self, resource_id: int | None = None, **params) -> T | None:
        """Get single resource by ID or with query params."""
        if resource_id:
            endpoint = f'{self.base_endpoint}/{resource_id}/'
        else:
            endpoint = f'{self.base_endpoint}/'

        response = self.session.request('GET', endpoint, params=params)
        return self.model_class(**response) if response else None

    def list(self, **params) -> list[T]:
        """List resources with optional query parameters."""
        response = self.session.request('GET', f'{self.base_endpoint}/', params=params)
        if not response:
            return []

        # Handle both list and paginated responses
        items = response if isinstance(response, list) else response.get('items', [])
        return [self.model_class(**item) for item in items]

    def create(self, data: dict[str, Any]) -> T | None:
        """Create new resource."""
        response = self.session.request('POST', f'{self.base_endpoint}/', json=data)
        return self.model_class(**response) if response else None

    def update(self, resource_id: int, data: dict[str, Any]) -> T | None:
        """Update existing resource."""
        endpoint = f'{self.base_endpoint}/{resource_id}/'
        response = self.session.request('PATCH', endpoint, json=data)
        return self.model_class(**response) if response else None

    def delete(self, resource_id: int) -> bool:
        """Delete resource."""
        try:
            endpoint = f'{self.base_endpoint}/{resource_id}/'
            self.session.request('DELETE', endpoint)
            return True
        except Exception:
            return False

    def action(self, resource_id: int | None, action: str, data: dict | None = None) -> Any:
        """Perform custom action on resource."""
        if resource_id:
            endpoint = f'{self.base_endpoint}/{resource_id}/{action}/'
        else:
            endpoint = f'{self.base_endpoint}/{action}/'

        method = 'POST' if data else 'GET'
        kwargs = {'json': data} if data else {}
        return self.session.request(method, endpoint, **kwargs)

    def custom_endpoint(self, path: str, method: str = 'GET', **kwargs) -> Any:
        """Make request to custom endpoint under this resource."""
        endpoint = f'{self.base_endpoint}/{path.lstrip("/")}'
        return self.session.request(method, endpoint, **kwargs)
