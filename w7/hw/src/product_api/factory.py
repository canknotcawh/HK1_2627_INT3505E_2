import os, logging, json, time
from flask import Flask, request, g
from .extensions import db, migrate
from .config import DefaultConfig
from .errors import register_errors
def create_app(config=None):
    app=Flask(__name__)
    app.config.from_object(config or DefaultConfig)
    db.init_app(app); migrate.init_app(app,db)
    from . import models
    from .blueprints import products,orders,health
    app.register_blueprint(products); app.register_blueprint(orders); app.register_blueprint(health)
    register_errors(app)
    app.logger.setLevel(app.config.get("LOG_LEVEL","INFO"))
    @app.before_request
    def start(): g.started=time.perf_counter()
    @app.after_request
    def log(response):
        app.logger.info(json.dumps({"event":"http_request","request_id":request.headers.get("X-Request-Id","-"),"status":response.status_code,"latency_ms":round((time.perf_counter()-g.started)*1000,2)}))
        return response
    @app.cli.command("init-db")
    def init_db():
        with app.app_context(): db.create_all()
        print("Tables created (development only; use migrations in managed environments).")
    return app
