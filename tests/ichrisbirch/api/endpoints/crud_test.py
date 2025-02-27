from fastapi import status
from fastapi.testclient import TestClient

from tests.util import show_status_and_response


class ApiCrudTester:

    def __init__(self, endpoint: str, new_obj):
        self.endpoint = endpoint
        self.new_obj = new_obj

    def item_id_by_position(self, test_api_logged_in: TestClient, position: int):
        all_obj = test_api_logged_in.get(self.endpoint)
        return all_obj.json()[position - 1]['id']

    def test_read_one(self, test_api_logged_in: TestClient):
        response = test_api_logged_in.get(f'{self.endpoint}1/')
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)

    def test_read_many(self, test_api_logged_in: TestClient):
        response = test_api_logged_in.get(self.endpoint)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 3 if 'users' not in self.endpoint else 5

    def test_create(self, test_api_logged_in: TestClient, verify_attr: str = 'name'):
        response = test_api_logged_in.post(self.endpoint, content=self.new_obj.model_dump_json())
        assert response.status_code == status.HTTP_201_CREATED, show_status_and_response(response)
        assert dict(response.json())[verify_attr] == getattr(self.new_obj, verify_attr)

        response = test_api_logged_in.get(self.endpoint)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert len(response.json()) == 4 if 'users' not in self.endpoint else 6

    def test_delete(self, test_api_logged_in: TestClient):
        all_obj = test_api_logged_in.get(self.endpoint)
        num_obj = len(all_obj.json())
        first_id = all_obj.json()[0]['id']
        response = test_api_logged_in.delete(f'{self.endpoint}{first_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(response)

        all_obj = test_api_logged_in.get(self.endpoint)
        assert len(all_obj.json()) == num_obj - 1

    def test_lifecycle(self, test_api_logged_in: TestClient, verify_attr: str = 'name'):
        all_obj = test_api_logged_in.get(self.endpoint)
        assert all_obj.status_code == status.HTTP_200_OK, show_status_and_response(all_obj)
        num_all_obj = len(all_obj.json())
        assert num_all_obj == 3

        created = test_api_logged_in.post(self.endpoint, content=self.new_obj.model_dump_json())
        assert created.status_code == status.HTTP_201_CREATED, show_status_and_response(created)
        assert created.json()[verify_attr] == getattr(self.new_obj, verify_attr)

        created_id = created.json().get('id')
        endpoint = f'{self.endpoint}{created_id}/'
        response = test_api_logged_in.get(endpoint)
        assert response.status_code == status.HTTP_200_OK, show_status_and_response(response)
        assert response.json()[verify_attr] == getattr(self.new_obj, verify_attr)

        all_obj_new = test_api_logged_in.get(self.endpoint)
        assert all_obj_new.status_code == status.HTTP_200_OK, show_status_and_response(all_obj_new)
        num_all_obj_new = len(all_obj_new.json())
        assert num_all_obj_new == num_all_obj + 1

        deleted = test_api_logged_in.delete(f'{self.endpoint}{created_id}/')
        assert deleted.status_code == status.HTTP_204_NO_CONTENT, show_status_and_response(deleted)

        all_obj_deleted = test_api_logged_in.get(self.endpoint)
        assert all_obj_deleted.status_code == status.HTTP_200_OK, show_status_and_response(all_obj_deleted)
        num_all_obj_deleted = len(all_obj_deleted.json())
        assert num_all_obj_deleted == num_all_obj_new - 1
