# db/schema.py
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, Column, Integer, String, Float, ForeignKey, DateTime, func

# Create metadata instance
metadata = MetaData()

# Define tables
users = Table(
    "users",
    metadata,
    Column("user_id", Integer, primary_key=True),
    Column("username", String, unique=True, nullable=False),
    Column("password", String, nullable=False),
    Column("email", String, unique=True, nullable=False),
    Column("role", String, nullable=False),
    Column("created_at", DateTime, default=func.now()),
)

products = Table(
    "products",
    metadata,
    Column("product_id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("description", String),
    Column("price", Float, nullable=False),
    Column("stock_quantity", Integer, nullable=False),
    Column("category", String),
    Column("image_url", String),
    Column("created_at", DateTime, default=func.now()),
)

cart_items = Table(
    "cart_items",
    metadata,
    Column("cart_id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.user_id"), nullable=False),
    Column("product_id", Integer, ForeignKey("products.product_id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("added_at", DateTime, default=func.now()),
)

orders = Table(
    "orders",
    metadata,
    Column("order_id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.user_id"), nullable=False),
    Column("total_amount", Float, nullable=False),
    Column("status", String, nullable=False),
    Column("created_at", DateTime, default=func.now()),
)

order_items = Table(
    "order_items",
    metadata,
    Column("item_id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.order_id"), nullable=False),
    Column("product_id", Integer, ForeignKey("products.product_id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("price_at_purchase", Float, nullable=False),
)

# Dictionary of all tables for easy access
tables = {
    "users": users,
    "products": products,
    "cart_items": cart_items,
    "orders": orders,
    "order_items": order_items
}

# SQL statements to create tables (for use by the Schema Agent)
create_tables_sql = {
    "users": """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "products": """
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock_quantity INTEGER NOT NULL,
        category TEXT,
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "cart_items": """
    CREATE TABLE IF NOT EXISTS cart_items (
        cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    """,
    "orders": """
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """,
    "order_items": """
    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price_at_purchase REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    """
}