# Test that when only creating the db and not inserting data that the db is fully created.
# check all tables, maybe parametrized by pytest
# from tests.conftest import ENGINE, get_testing_session

# def test_insert_data(insert_test_data):
#     """Test that the data was inserted into the db"""
#     session = next(get_testing_session())
#     Base.metadata.create_all(ENGINE)
#     records = session.query(models.Task).all()
#     assert len(records) == 3
#     session.close()


# def test_create_app(test_app):
#     """Test that the app was created"""
#     assert test_app is not None


# def test_api(test_api):
#     """Test that the api was created"""
#     assert test_api is not None


# def test_db(test_db):
#     """Test that the db was created"""
#     assert test_db is not None


# def test_app_client(test_app_client):
#     """Test that the app client was created"""
#     assert test_app_client is not None


# def test_api_client(test_api_client):
#     """Test that the api client was created"""
#     assert test_api_client is not None


# def test_app_db(test_app_db):
#     """Test that the app db was created"""
#     assert test_app_db is not None


# def test_api_db(test_api_db):
#     """Test that the api db was created"""
#     assert test_api_db is not None


# def test_app_session(test_app_session):
#     """Test that the app session was created"""
#     assert test_app_session is not None


# def test_api_session(test_api_session):
#     """Test that the api session was created"""
#     assert test_api_session is not None


# def test_app_engine(test_app_engine):
#     """Test that the app engine was created"""
#     assert test_app_engine is not None


# def test_api_engine(test_api_engine):
#     """Test that the api engine was created"""
#     assert test_api_engine is not None


# def test_app_settings(test_app_settings):
#     """Test that the app settings were created"""
#     assert test_app_settings is not None


# def test_api_settings(test_api_settings):
#     """Test that the api settings were created"""
#     assert test_api_settings is
