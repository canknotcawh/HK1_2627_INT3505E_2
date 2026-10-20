import os
from flask import Flask, jsonify
from bookstore_api import db
from bookstore_api.models import Author, Book, Category, User
from bookstore_api.routes import api


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///bookstore.db"), SQLALCHEMY_TRACK_MODIFICATIONS=False)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    app.register_blueprint(api)

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    with app.app_context():
        db.create_all()
        if app.config.get("SEED_DATA", True) and Category.query.count() == 0:
            fiction = Category(name="Fiction", slug="fiction")
            tech = Category(name="Technology", slug="technology")
            db.session.add_all([fiction, tech])
            db.session.flush()
            authors = [Author(name="Nguyen Van A", bio="Vietnamese writer"), Author(name="Le Thi B", bio="Computer science author")]
            db.session.add_all(authors)
            db.session.flush()
            books = [Book(title="The River", isbn="9780000000001", price_vnd=120000, stock=8, genre="fiction", category_id=fiction.id, authors=[authors[0]]),
                     Book(title="API Design", isbn="9780000000002", price_vnd=250000, stock=5, genre="technology", category_id=tech.id, authors=[authors[1]]),
                     Book(title="Blue Mountain", isbn="9780000000003", price_vnd=160000, stock=3, genre="fiction", category_id=fiction.id, authors=[authors[0], authors[1]])]
            db.session.add_all(books)
            db.session.add(User(email="reader@example.com", display_name="Reader One"))
            db.session.commit()
    return app


app = create_app()
