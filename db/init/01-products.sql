CREATE TABLE IF NOT EXISTS products (
  id    SERIAL PRIMARY KEY,
  name  TEXT NOT NULL,
  price NUMERIC(10,2) NOT NULL,
  stock INTEGER NOT NULL CHECK (stock >= 0)
);

INSERT INTO products (name, price, stock) VALUES
  ('Mechanical Keyboard', 59.00, 20),
  ('Wireless Mouse',      19.50, 50),
  ('USB-C Hub',           25.00, 0);