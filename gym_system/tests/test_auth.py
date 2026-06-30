import pytest
from app import create_app
from database.db import db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
        yield c

def test_login_page(client):
    r = client.get('/auth/login')
    assert r.status_code == 200

def test_invalid_login(client):
    r = client.post('/auth/login', data={'username': 'fake', 'password': 'wrong'})
    assert r.status_code in (200, 302)
