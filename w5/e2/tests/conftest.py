import pytest
from app import create_app
from bookstore_api import db


@pytest.fixture()
def client():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "SQLALCHEMY_ENGINE_OPTIONS": {"poolclass": __import__("sqlalchemy").pool.StaticPool}, "SEED_DATA": True})
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()
