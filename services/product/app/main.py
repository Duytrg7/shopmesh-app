from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="product-service", version="0.1.0")


class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int


# Seed data in code (Day 4 moves this to PostgreSQL)
PRODUCTS: dict[int, Product] = {
    1: Product(id=1, name="Mechanical Keyboard", price=59.0, stock=20),
    2: Product(id=2, name="Wireless Mouse", price=19.5, stock=50),
    3: Product(id=3, name="USB-C Hub", price=25.0, stock=0),
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/products", response_model=list[Product])
def list_products():
    return list(PRODUCTS.values())


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    product = PRODUCTS.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product