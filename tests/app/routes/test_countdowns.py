from ichrisbirch.app.routes.countdowns import COUNTDOWNS_URL


def test_index(test_app):
    response = test_app.get(COUNTDOWNS_URL + '/')
    assert response.status_code == 200
    assert b'<title>Countdowns</title>' in response.data


def test_crud_add(test_app):
    data = {
        'name': 'Countdown 1',
        'due_date': '2022-01-01',
        'method': 'add',
    }
    response = test_app.post(COUNTDOWNS_URL + '/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/countdowns/'
    assert b'<title>Countdowns</title>' in response.data


def test_crud_delete(test_app):
    data = {
        'id': 1,
        'method': 'delete',
    }
    response = test_app.post(COUNTDOWNS_URL + '/crud/', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert len(response.history) == 1
    assert response.request.path == '/countdowns/'
    assert b'<title>Countdowns</title>' in response.data
