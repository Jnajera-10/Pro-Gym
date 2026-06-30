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

def test_clients_requires_login(client):
    r = client.get('/clients/')
    assert r.status_code in (302, 401)
