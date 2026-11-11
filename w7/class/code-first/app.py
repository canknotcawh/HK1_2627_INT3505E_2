from flask import Flask
from flask_smorest import Api, Blueprint
from marshmallow import Schema, fields
from flask.views import MethodView

app = Flask(__name__)

app.config["API_TITLE"] = "Product API"
app.config["API_VERSION"] = "1.0.0"
app.config["OPENAPI_VERSION"] = "3.0.3"

app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = (
    "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
)

api = Api(app)


class ProductSchema(Schema):
    id = fields.Int(dump_only=True)

    name = fields.Str(
        required=True,
        metadata={
            "description": "The name of the product",
            "example": "Apple iPhone 36"
        }
    )

    price = fields.Float(
        required=True,
        metadata={
            "description": "The price of the product",
            "example": 999.99
        }
    )

    description = fields.Str(
        required=False,
        metadata={
            "description": "The description of the product",
            "example": "A high-end smartphone"
        }
    )

products = []
next_id = 1

product_blp = Blueprint(
    "products",
    "products",
    url_prefix="/api/v1/products",
    description="Product management API"
)

@product_blp.route("/")
class ProductList(MethodView):

    @product_blp.response(200, ProductSchema(many=True))
    def get(self):
        """Get all products"""
        return products

    @product_blp.arguments(ProductSchema)
    @product_blp.response(201, ProductSchema)
    def post(self, new_product):
        """Create a new product"""

        global next_id

        new_product["id"] = next_id
        next_id += 1

        products.append(new_product)

        return new_product

api.register_blueprint(product_blp)

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
