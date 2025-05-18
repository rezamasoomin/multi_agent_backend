# tools/db_tools.py
from typing import Dict, List, Any, Optional, Tuple
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config.settings import DATABASE_URL

def execute_sql_query(query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
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
    from db.schema import create_tables_sql
    
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

def insert_sample_data() -> Dict[str, Any]:
    """Insert sample data into the database for testing."""
    # Sample admin user
    admin_query = """
    INSERT INTO users (username, password, email, role)
    VALUES (:username, :password, :email, :role)
    ON CONFLICT (username) DO NOTHING
    """
    admin_params = {
        "username": "admin",
        "password": "admin123",  # In production, use hashed passwords
        "email": "admin@example.com",
        "role": "admin"
    }
    
    # Sample customer user
    customer_query = """
    INSERT INTO users (username, password, email, role)
    VALUES (:username, :password, :email, :role)
    ON CONFLICT (username) DO NOTHING
    """
    customer_params = {
        "username": "customer",
        "password": "customer123",  # In production, use hashed passwords
        "email": "customer@example.com",
        "role": "customer"
    }
    
    # Sample products
    products_query = """
    INSERT INTO products (name, description, price, stock_quantity, category, image_url)
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
    
    # Execute queries
    results = {}
    
    admin_result = execute_sql_query(admin_query, admin_params)
    results["admin_user"] = admin_result
    
    customer_result = execute_sql_query(customer_query, customer_params)
    results["customer_user"] = customer_result
    
    products_results = []
    for params in products_params:
        product_result = execute_sql_query(products_query, params)
        products_results.append(product_result)
    results["products"] = products_results
    
    return {"success": True, "message": "Sample data inserted successfully", "results": results}