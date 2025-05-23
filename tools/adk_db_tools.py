# tools/adk_db_tools.py
from typing import Dict, Any
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config.settings import DATABASE_URL

def search_products(search_term: str) -> Dict[str, Any]:
    """Search for products in the database.
    
    Args:
        search_term: Term to search for in product names and descriptions. Use empty string for all products.
        
    Returns:
        Dictionary with search results in json format
        example:
        {
            "success": true,
            "data": [
                {
                    "product_id": 1,
                    "name": "Product A",
                    "description": "Description of Product A",
                    "price": 19.99,
                    "stock_quantity": 10,
                    "category": "Category A",
                    "image_url": "http://example.com/image_a.jpg"
                },
                ...
            ],
            "message": "Found X products matching 'search_term'"
        }
    """
    print(f"DEBUG: search_products called with search_term='{search_term}'")
    
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as connection:
            if search_term.strip():
                query = text("""
                    SELECT product_id, name, description, price, stock_quantity, category, image_url
                    FROM products 
                    WHERE (name LIKE :search_term OR description LIKE :search_term) 
                    AND stock_quantity > 0
                    ORDER BY name
                """)
                result = connection.execute(query, {"search_term": f"%{search_term}%"})
            else:
                query = text("""
                    SELECT product_id, name, description, price, stock_quantity, category, image_url
                    FROM products 
                    WHERE stock_quantity > 0
                    ORDER BY name
                    LIMIT 10
                """)
                result = connection.execute(query)
            
            columns = result.keys()
            products = []
            for row in result:
                products.append(dict(zip(columns, row)))
            
            response = {
                "success": True,
                "data": products,
                "message": f"Found {len(products)} products" + (f" matching '{search_term}'" if search_term.strip() else "")
            }
            
            return response
            
    except SQLAlchemyError as e:
        error_response = {
            "success": False,
            "error": str(e),
            "message": "Failed to search products"
        }
        print(f"DEBUG: search_products error: {error_response}")
        return error_response

def get_user_cart(user_id: str) -> Dict[str, Any]:
    """Get cart items for a specific user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with cart contents
    """
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT ci.cart_id, ci.quantity, ci.added_at,
                       p.product_id, p.name, p.price, p.description,
                       (ci.quantity * p.price) as total_price
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.product_id
                WHERE ci.user_id = :user_id
                ORDER BY ci.added_at DESC
            """)
            
            result = connection.execute(query, {"user_id": int(user_id)})
            
            columns = result.keys()
            cart_items = []
            total_amount = 0
            
            for row in result:
                item = dict(zip(columns, row))
                cart_items.append(item)
                total_amount += item.get("total_price", 0)
            
            return {
                "success": True,
                "data": {
                    "cart_items": cart_items,
                    "total_amount": round(total_amount, 2),
                    "item_count": len(cart_items)
                },
                "message": f"Cart contains {len(cart_items)} items with total ${total_amount:.2f}"
            }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve cart"
        }

def get_user_orders(user_id: str) -> Dict[str, Any]:
    """Get order history for a specific user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with order history
    """
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as connection:
            query = text("""
                SELECT order_id, total_amount, status, created_at
                FROM orders
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT 20
            """)
            
            result = connection.execute(query, {"user_id": int(user_id)})
            
            columns = result.keys()
            orders = []
            
            for row in result:
                orders.append(dict(zip(columns, row)))
            
            return {
                "success": True,
                "data": orders,
                "message": f"Found {len(orders)} orders"
            }
    except SQLAlchemyError as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve orders"
        }