# main.py
import os
import google.generativeai as genai
import uvicorn
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Import ADK components
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner

# Import our modules
from config.settings import DATABASE_URL, GOOGLE_API_KEY, GEMINI_MODEL, SYSTEM_USER_ID
from agents.schema_agent import create_schema_agent
from agents.user_agent import create_user_agent
from agents.product_agent import create_product_agent
from agents.cart_agent import create_cart_agent
from agents.order_agent import create_order_agent
from agents.main_agent import create_main_agent

# Import API app and routes
from api.app import app, get_current_user, verify_admin
from api.admin_routes import (
    admin_router, ProductRequest, ProductUpdateRequest, 
    OrderStatusUpdateRequest, MessageRequest as AdminMessageRequest
)
from api.customer_routes import (
    customer_router, CartItemRequest, 
    MessageRequest as CustomerMessageRequest
)

# Initialize Google Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = 'gemini-2.0-flash' #genai.GenerativeModel(GEMINI_MODEL)

# Initialize database session service
session_service = DatabaseSessionService(db_url=DATABASE_URL)

# Initialize agents
schema_agent = create_schema_agent(model)
user_agent = create_user_agent(model)
product_agent = create_product_agent(model)
cart_agent = create_cart_agent(model)
order_agent = create_order_agent(model)
main_agent = create_main_agent(model)

# Initialize runners
schema_runner = Runner(agent= schema_agent,app_name='schema', session_service=session_service)
user_runner = Runner(agent=user_agent,app_name='user', session_service=session_service)
product_runner = Runner(agent=product_agent,app_name= 'product',session_service=session_service)
cart_runner = Runner(agent=cart_agent, app_name='cart',session_service=session_service)
order_runner = Runner(agent=order_agent,app_name='order', session_service=session_service)
main_runner = Runner(agent=main_agent,app_name='main', session_service=session_service)

# Register routers
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(customer_router, prefix="/api/customer", tags=["Customer"])

# Initialize database on startup
@app.on_event("startup")
async def initialize_database():
    # Create schema
    schema_response = schema_runner.run(
        user_id=SYSTEM_USER_ID,
        content="Initialize the database schema for our e-commerce application"
    )
    print("Schema creation response:", schema_response)
    
    # Insert sample data
    data_response = schema_runner.run(
        user_id=SYSTEM_USER_ID,
        content="Insert sample data for testing our e-commerce application"
    )
    print("Sample data insertion response:", data_response)

# Admin routes
@admin_router.post("/products", tags=["Products"])
async def add_product(
    product: ProductRequest, 
    user: Dict[str, Any] = Depends(verify_admin)
):
    """Add a new product (admin only)"""
    product_content = f"""
    Add a new product with the following details:
    - Name: {product.name}
    - Price: {product.price}
    - Stock Quantity: {product.stock_quantity}
    - Description: {product.description or "N/A"}
    - Category: {product.category or "N/A"}
    - Image URL: {product.image_url or "N/A"}
    """
    response = product_runner.run(user_id=str(user["user_id"]), content=product_content)
    return response

@admin_router.put("/products/{product_id}", tags=["Products"])
async def update_product(
    product_id: int,
    product: ProductUpdateRequest,
    user: Dict[str, Any] = Depends(verify_admin)
):
    """Update a product (admin only)"""
    # Build update fields string
    update_fields = []
    if product.name is not None:
        update_fields.append(f"- Name: {product.name}")
    if product.price is not None:
        update_fields.append(f"- Price: {product.price}")
    if product.stock_quantity is not None:
        update_fields.append(f"- Stock Quantity: {product.stock_quantity}")
    if product.description is not None:
        update_fields.append(f"- Description: {product.description}")
    if product.category is not None:
        update_fields.append(f"- Category: {product.category}")
    if product.image_url is not None:
        update_fields.append(f"- Image URL: {product.image_url}")
    
    update_text = "\n".join(update_fields)
    
    message = f"""
    Update product with ID {product_id} with the following changes:
    {update_text}
    """
    response = product_runner.run(user_id=str(user["user_id"]), message=message)
    return response

# Add more admin routes here...

# Customer routes
@customer_router.get("/products", tags=["Products"])
async def list_products(
    category: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """List all products, optionally filtered by category"""
    if category:
        message = f"Show me all products in the {category} category"
    else:
        message = "Show me all available products"
    
    response = product_runner.run(user_id=str(user["user_id"]), message=message)
    return response

@customer_router.get("/cart", tags=["Cart"])
async def view_cart(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """View the current user's shopping cart"""
    message = "Show me my current shopping cart"
    response = cart_runner.run(user_id=str(user["user_id"]), message=message)
    return response

# Add more customer routes here...

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)