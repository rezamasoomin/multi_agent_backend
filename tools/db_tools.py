# tools/db_tools.py
from typing import Dict, List, Any, Optional, Tuple
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from config.settings import DATABASE_URL

def execute_sql_query(query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Execute a SQL query and return results.
    
    Args:
        query: SQL query to execute
        params: Parameters for the query
        
    Returns:
        Dictionary with query results or error
    """
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            connection.commit()  # Add explicit commit
            
            if query.strip().upper().startswith(("SELECT", "WITH")):
                # For SELECT queries, return the results
                columns = result.keys()
                rows = []
                for row in result:
                    rows.append(dict(zip(columns, row)))
                return {"success": True, "data": rows}
            else:
                # For non-SELECT queries, return affected row count
                return {"success": True, "rowcount": result.rowcount}
    except SQLAlchemyError as e:
        return {"success": False, "error": str(e)}

def create_database_schema() -> Dict[str, Any]:
    """Create the initial database schema for the e-commerce application."""
    # SQL statements to create tables
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
            name TEXT UNIQUE NOT NULL,
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
    
    results = {}
    for table_name, sql in create_tables_sql.items():
        result = execute_sql_query(sql)
        results[table_name] = result
        
        if not result["success"]:
            return {
                "success": False, 
                "error": f"Failed to create table '{table_name}': {result['error']}",
                "results": results
            }
    
    return {"success": True, "message": "Database schema created successfully", "results": results}

def check_if_data_exists() -> bool:
    """Check if sample data already exists in the database."""
    query = "SELECT COUNT(*) as count FROM users WHERE username IN ('admin', 'customer')"
    result = execute_sql_query(query)
    
    if result["success"] and result["data"]:
        return result["data"][0]["count"] > 0
    return False

def insert_sample_data() -> Dict[str, Any]:
    """Insert sample data into the database for testing."""
    
    # Check if data already exists
    if check_if_data_exists():
        return {
            "success": True, 
            "message": "Sample data already exists, skipping insertion",
            "results": {"skipped": True}
        }
    
    results = {}
    
    try:
        # Sample admin user - using INSERT OR IGNORE
        admin_query = """
        INSERT OR IGNORE INTO users (username, password, email, role)
        VALUES (:username, :password, :email, :role)
        """
        admin_params = {
            "username": "admin",
            "password": "admin123",  # In production, use hashed passwords
            "email": "admin@example.com",
            "role": "admin"
        }
        
        admin_result = execute_sql_query(admin_query, admin_params)
        results["admin_user"] = admin_result
        print(f"Admin user result: {admin_result}")
        
        # Sample customer user - using INSERT OR IGNORE
        customer_query = """
        INSERT OR IGNORE INTO users (username, password, email, role)
        VALUES (:username, :password, :email, :role)
        """
        customer_params = {
            "username": "customer",
            "password": "customer123",  # In production, use hashed passwords
            "email": "customer@example.com",
            "role": "customer"
        }
        
        customer_result = execute_sql_query(customer_query, customer_params)
        results["customer_user"] = customer_result
        print(f"Customer user result: {customer_result}")
        
        # Sample products - using INSERT OR IGNORE
        products_query = """
        INSERT OR IGNORE INTO products (name, description, price, stock_quantity, category, image_url)
        VALUES (:name, :description, :price, :stock_quantity, :category, :image_url)
        """
        products_params = [
            {
                "name": "Smartphone X",
                "description": "Latest smartphone with amazing features",
                "price": 499.99,
                "stock_quantity": 50,
                "category": "Electronics",
                "image_url": "https://example.com/smartphone.jpg"
            },
            {
                "name": "Laptop Pro",
                "description": "Powerful laptop for professionals",
                "price": 1299.99,
                "stock_quantity": 20,
                "category": "Electronics",
                "image_url": "https://example.com/laptop.jpg"
            },
            {
                "name": "Casual T-Shirt",
                "description": "Comfortable cotton t-shirt",
                "price": 19.99,
                "stock_quantity": 100,
                "category": "Clothing",
                "image_url": "https://example.com/tshirt.jpg"
            }
        ]
        
        products_results = []
        for params in products_params:
            product_result = execute_sql_query(products_query, params)
            products_results.append(product_result)
            print(f"Product insertion result: {product_result}")
        
        results["products"] = products_results
        
        # Check if any data was actually inserted
        success_count = 0
        if admin_result.get("success") and admin_result.get("rowcount", 0) > 0:
            success_count += 1
        if customer_result.get("success") and customer_result.get("rowcount", 0) > 0:
            success_count += 1
        for prod_result in products_results:
            if prod_result.get("success") and prod_result.get("rowcount", 0) > 0:
                success_count += 1
                
        if success_count > 0:
            return {"success": True, "message": f"Sample data inserted successfully ({success_count} new records)", "results": results}
        else:
            return {"success": True, "message": "No new data inserted (may already exist)", "results": results}
            
    except Exception as e:
        return {"success": False, "error": f"Error inserting sample data: {str(e)}", "results": results}

def get_all_users() -> Dict[str, Any]:
    """Get all users from the database for verification."""
    query = "SELECT user_id, username, email, role, created_at FROM users"
    return execute_sql_query(query)

def get_all_products() -> Dict[str, Any]:
    """Get all products from the database for verification."""
    query = "SELECT product_id, name, description, price, stock_quantity, category FROM products"
    return execute_sql_query(query)