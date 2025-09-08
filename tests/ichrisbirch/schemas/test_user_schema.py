"""Tests for the user schema validation.

Tests that the User, UserCreate, and UserUpdate schemas properly validate data.
"""

import datetime

import pytest
from pydantic import ValidationError

from ichrisbirch.schemas.user import User
from ichrisbirch.schemas.user import UserCreate
from ichrisbirch.schemas.user import UserUpdate


class TestUserSchema:
    def test_user_create_valid(self):
        """Test creating a valid UserCreate model."""
        user_data = {'name': 'Test User', 'email': 'test@example.com', 'password': 'strongpassword123'}
        user = UserCreate(**user_data)
        assert user.name == 'Test User'
        assert user.email == 'test@example.com'
        assert user.password == 'strongpassword123'

    def test_user_create_invalid_missing_fields(self):
        """Test UserCreate fails with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(name='Test User', email='test@example.com')

        errors = exc_info.value.errors()
        assert any(err['type'] == 'missing' and err['loc'][0] == 'password' for err in errors)

    def test_user_create_invalid_empty_fields(self):
        """Test UserCreate fails with empty fields."""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(name='', email='test@example.com', password='strongpassword123')

        errors = exc_info.value.errors()
        assert any(err['loc'][0] == 'name' for err in errors)

    def test_user_model_valid(self):
        """Test creating a valid User model."""
        now = datetime.datetime.now()
        user_data = {
            'id': 1,
            'alternative_id': 12345,
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'hashed_password_string',
            'is_admin': False,
            'created_on': now,
            'last_login': now,
            'preferences': {'theme': 'dark'},
        }
        user = User(**user_data)
        assert user.id == 1
        assert user.name == 'Test User'
        assert user.email == 'test@example.com'
        assert user.is_admin is False
        assert isinstance(user.preferences, dict)
        assert user.preferences['theme'] == 'dark'

    def test_user_model_missing_fields(self):
        """Test User model fails with missing required fields."""
        now = datetime.datetime.now()
        incomplete_data = {
            'id': 1,
            'name': 'Test User',
            'email': 'test@example.com',
            'is_admin': False,
            'created_on': now,
            'preferences': {},
        }

        with pytest.raises(ValidationError):
            User(**incomplete_data)

    def test_user_update_valid(self):
        """Test creating a valid UserUpdate model."""
        now = datetime.datetime.now()
        update_data = {'name': 'Updated Name', 'last_login': now, 'preferences': {'theme': 'light'}}
        user_update = UserUpdate(**update_data)
        assert user_update.name == 'Updated Name'
        assert user_update.last_login == now
        assert user_update.preferences['theme'] == 'light'
        assert user_update.email is None
        assert user_update.password is None

    def test_user_update_empty(self):
        """Test creating an empty UserUpdate is valid (all fields optional)."""
        user_update = UserUpdate()
        assert user_update.name is None
        assert user_update.email is None
        assert user_update.password is None
        assert user_update.last_login is None
        assert user_update.preferences is None

    def test_user_update_partial(self):
        """Test updating only specific fields."""
        user_update = UserUpdate(name='New Name')
        assert user_update.name == 'New Name'
        assert user_update.email is None
        assert user_update.password is None
