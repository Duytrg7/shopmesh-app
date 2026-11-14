# product service – ShopMesh
# Serves the product catalog (name, price, stock) from PostgreSQL over HTTP/JSON.
# Called by: frontend (list products), cart + order (check price / stock).

import os  # read environment variables (configuration comes from outside the code)

import psycopg                      # PostgreSQL driver: lets Python talk to Postgres
from psycopg.rows import dict_row   # return each DB row as a dict {"id": 1, "name": ...}
from fastapi import FastAPI, HTTPException  # web framework + way to return HTTP errors
from pydantic import BaseModel              # data model: validates types, converts to JSON

# Connection string, e.g. postgresql://user:password@host:port/database
# Set by `export` (local) or docker-compose `environment:` (container).
# No default value on purpose: if it is missing the app crashes at startup
# with KeyError (fail fast) instead of silently using a hard-coded password.
DATABASE_URL = os.environ["DATABASE_URL"]

# The FastAPI app. title/version show up on the auto-generated /docs page.
# 0.2.0 = MINOR bump (semver): new feature, data now comes from the database.
app = FastAPI(title="product-service", version="0.3.0")


class Product(BaseModel):
    """Shape of one product in every response (the API 'contract')."""
    id: int
    name: str
    price: float  # stored as NUMERIC(10,2) in Postgres, sent as a JSON number
    stock: int


def get_conn():
    """Open a new connection to Postgres.

    One connection per request keeps the code simple for now.
    (Later: a connection pool to reuse connections under load.)
    """
    # connect_timeout=3 → give up after 3 seconds instead of hanging
    # (important for /ready: a probe must answer fast)
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=3)


@app.get("/health")
def health():
    """Liveness check: answers 200 as long as the process is running.

    Used later by Kubernetes probes and Istio. It does NOT check the database,
    so it stays green even if Postgres is down (we test this in Step 3).
    """
    return {"status": "ok"}

@app.get("/ready")
def ready():
    """Readiness check: can this instance serve requests right now?

    Unlike /health, it checks the dependency (Postgres).
    200 → send me traffic; 503 → keep me alive but stop sending traffic.
    Kubernetes (W2): readinessProbe → /ready, livenessProbe → /health.
    """
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")  # cheapest possible query: "are you there?"
    except psycopg.OperationalError:
        # 503 Service Unavailable = "alive, but temporarily cannot serve"
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ready"}

@app.get("/products", response_model=list[Product])
def list_products():
    """GET /products → every product, ordered by id."""
    # `with` opens the connection and closes it automatically at the end of the block
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, name, price, stock FROM products ORDER BY id"
        ).fetchall()  # list of dicts → FastAPI turns it into a JSON array


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """GET /products/{id} → one product, or 404 if the id does not exist.

    `product_id: int` → FastAPI rejects non-numbers (e.g. "abc") with 422.
    """
    with get_conn() as conn:
        row = conn.execute(
            # %s = placeholder; psycopg sends the value separately and escapes it
            # → no SQL injection. Never build SQL with f-strings / string concat.
            "SELECT id, name, price, stock FROM products WHERE id = %s",
            (product_id,),  # parameters go in a tuple; the comma makes it a 1-item tuple
        ).fetchone()        # first matching row, or None if there is no match
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return row