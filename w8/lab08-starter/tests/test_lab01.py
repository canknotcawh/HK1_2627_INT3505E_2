
import pytest
from jsonschema import validate, ValidationError
from tools import get_book_schema


def clear_books(app):
    from models import Book, db

    with app.app_context():
        db.session.query(Book).delete()
        db.session.commit()


def test_get_books_empty_db(client, app):
    clear_books(app)

    response = client.get("/books")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_book_not_found(client, app):
    clear_books(app)

    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_post_book_missing_title(client, app):
    clear_books(app)

    response = client.post(
        "/books",
        json={"author": "Author Only"}
    )

    assert response.status_code == 400

    data = response.get_json()
    assert any(
        item["field"] == "title"
        for item in data["errors"]
    )


def test_post_delete_get_book(client, app, sample_book):
    # sample_book is the ID of a book already created by conftest
    book_id = sample_book

    delete_response = client.delete(f"/books/{book_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 404
    assert get_response.get_json()["code"] == "NOT_FOUND"


def test_book_response_schema_validation(client, app, sample_book):
    # sample_book is the ID of an existing book
    response = client.get(f"/books/{sample_book}")

    assert response.status_code == 200

    book_response = response.get_json()
    schema = get_book_schema()

    # Original response must satisfy JSON Schema
    validate(instance=book_response, schema=schema)

    # Copy response and add an unknown field
    invalid_response = book_response.copy()
    invalid_response["unknown_field"] = "unexpected"

    with pytest.raises(ValidationError):
        validate(instance=invalid_response, schema=schema)
