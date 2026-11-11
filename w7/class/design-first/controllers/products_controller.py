products = []

next_id = 1

def get_products():

    return products, 200

def create_product(body):

    global next_id

    new_product = {
        "id": next_id,
        "name": body["name"],
        "price": body["price"],
        "description": body.get("description", "")
    }

    next_id += 1

    products.append(new_product)

    return new_product, 201