
import pytest
from app import create_app
from extensions import db
@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
def test_signup(client):
    response = client.post('/signup', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200

def test_login(client):
    client.post('/signup', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
