from ichrisbirch.models import User

BASE_DATA: list[User] = [
    User(
        name='Regular User 1',
        email='regular_user_1@gmail.com',
        password='regular_user_1',
        is_admin=False,
    ),
    User(
        name='Regular User 2',
        email='regular.user.2@hotmail.com',
        password='regular_user_2',
    ),
    User(
        name='Admin User',
        email='admin@admin.com',
        password='adminpassword',
        is_admin=True,
    ),
]
