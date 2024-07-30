from fastapi import status
from fastapi.testclient import TestClient

from ichrisbirch import models
from tests.util import log_all_table_items
from tests.util import show_status_and_response


class ApiCrudTester:

    def __init__(self, endpoint: str, new_obj):
        self.endpoint = endpoint
        self.new_obj = new_obj

    def item_id_by_position(self, test_api: TestClient, position: int):
        all_obj = test_api.get(self.endpoint)
        return all_obj.json()[position - 1]['id']

    def test_read_one(self, test_api: TestClient):
        response = test_api.get(f'{self.endpoint}1/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    def test_read_many(self, test_api: TestClient):
        response = test_api.get(self.endpoint)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 3 if 'users' not in self.endpoint else 5

    def test_create(self, test_api: TestClient, verify_attr: str = 'name'):
        response = test_api.post(self.endpoint, content=self.new_obj.model_dump_json())
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        assert dict(response.json())[verify_attr] == getattr(self.new_obj, verify_attr)

        response = test_api.get(self.endpoint)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 4 if 'users' not in self.endpoint else 6

    def test_delete(self, test_api: TestClient):
        all_obj = test_api.get(self.endpoint)
        num_obj = len(all_obj.json())
        first_id = all_obj.json()[0]['id']

        response = test_api.delete(f'{self.endpoint}{first_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

        all_obj = test_api.get(self.endpoint)
        assert len(all_obj.json()) == num_obj - 1

    def test_lifecycle(self, test_api: TestClient, verify_attr: str = 'name'):
        all_obj = test_api.get(self.endpoint)
        assert all_obj.status_code == status.HTTP_200_OK, show_status_and_response(all_obj)
        num_all_obj = len(all_obj.json())
        log_all_table_items('users', models.User, 'name')
        assert num_all_obj == 3

        created = test_api.post(self.endpoint, content=self.new_obj.model_dump_json())
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()[verify_attr] == getattr(self.new_obj, verify_attr)

        created_id = created.json().get('id')
        endpoint = f'{self.endpoint}{created_id}/'
        response = test_api.get(endpoint)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()[verify_attr] == getattr(self.new_obj, verify_attr)

        all_obj_new = test_api.get(self.endpoint)
        assert all_obj_new.status_code == status.HTTP_200_OK, show_status_and_response(all_obj_new)
        num_all_obj_new = len(all_obj_new.json())
        assert num_all_obj_new == num_all_obj + 1

        deleted = test_api.delete(f'{self.endpoint}{created_id}/')
        assert deleted.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted)

        all_obj_deleted = test_api.get(self.endpoint)
        assert all_obj_deleted.status_code == status.HTTP_200_OK, show_status_and_response(all_obj_deleted)
        num_all_obj_deleted = len(all_obj_deleted.json())
        assert num_all_obj_deleted == num_all_obj_new - 1
