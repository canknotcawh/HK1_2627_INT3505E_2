from connexion import FlaskApp

app = FlaskApp(
    __name__,
    specification_dir="openapi"
)

app.add_api(
    "openapi.yaml",
    validate_responses=True
)

if __name__ == "__main__":
    app.run(port=5000)