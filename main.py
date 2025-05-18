import os
import uuid
import google.generativeai as genai
import uvicorn
from fastapi import Depends # Removed HTTPException as it's handled in api.app or not used directly here
from pydantic import BaseModel # Not strictly needed here if models are imported with routers
from typing import Dict, Any, Optional, List, Generator

# Import ADK components
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.adk.events.event import Event

# Import your project's modules
from config.settings import DATABASE_URL, GOOGLE_API_KEY, GEMINI_MODEL, SYSTEM_USER_ID
from agents.schema_agent import create_schema_agent
from agents.user_agent import create_user_agent
from agents.product_agent import create_product_agent
from agents.cart_agent import create_cart_agent
from agents.order_agent import create_order_agent
from agents.main_agent import create_main_agent

# 1. Import the main 'app' instance and shared dependencies (like auth)
from api.app import app, get_current_user, verify_admin

# 2. Import the routers and their Pydantic models
from api.admin_routes import admin_router, ProductRequest, ProductUpdateRequest, OrderStatusUpdateRequest
# Removed: MessageRequest as AdminMessageRequest (unless used)
from api.customer_routes import customer_router, CartItemRequest
# Removed: MessageRequest as CustomerMessageRequest (unless used)


# Initialize Google Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = 'gemini-2.0-flash'

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
schema_runner = Runner(agent=schema_agent, app_name='schema', session_service=session_service)
user_runner = Runner(agent=user_agent, app_name='user', session_service=session_service)
product_runner = Runner(agent=product_agent, app_name='product', session_service=session_service)
cart_runner = Runner(agent=cart_agent, app_name='cart', session_service=session_service)
order_runner = Runner(agent=order_agent, app_name='order', session_service=session_service)
main_runner = Runner(agent=main_agent, app_name='main', session_service=session_service)


# Helper to process runner generator
def process_run_response(response_generator: Generator[Event, None, None]) -> List[Dict]:
    events = []
    for event in response_generator:
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts') and event.content.parts:
                text_parts = [part.text for part in event.content.parts if hasattr(part, 'text')]
                events.append({"author": event.author, "text": " ".join(text_parts)})
            elif hasattr(event.content, 'text'):
                events.append({"author": event.author, "text": event.content.text})
            else:
                events.append({"author": event.author, "content": str(event.content)})
        else:
            events.append({"author": event.author, "event_type": type(event).__name__})
    return events

# Initialize database on startup
@app.on_event("startup")
async def initialize_database():
    session_id_for_init = str(uuid.uuid4())
    schema_message_text = "Initialize the database schema for our e-commerce application"
    print(f"Initializing schema with user_id: {SYSTEM_USER_ID}, session_id: {session_id_for_init}")
    try:
        # If your session_service.get_session in Runner.run_async doesn't auto-create,
        # you might need to explicitly create it first:
        # await session_service.create_session(app_name='schema', user_id=SYSTEM_USER_ID, session_id=session_id_for_init)
        schema_response_gen = schema_runner.run(
            user_id=SYSTEM_USER_ID,
            session_id=session_id_for_init,
            new_message=schema_message_text
        )
        print("Schema creation response (generator object):", schema_response_gen)
        # list(schema_response_gen) # Consume generator if needed for side effects
    except Exception as e:
        print(f"Error during schema initialization: {e}") # Consider logging properly
        # raise # Or handle gracefully

    sample_data_text = "Insert sample data for testing our e-commerce application"
    print(f"Inserting sample data with user_id: {SYSTEM_USER_ID}, session_id: {session_id_for_init}")
    try:
        # await session_service.create_session(app_name='schema', user_id=SYSTEM_USER_ID, session_id=session_id_for_init) # If needed
        data_response_gen = schema_runner.run(
            user_id=SYSTEM_USER_ID,
            session_id=session_id_for_init,
            new_message=sample_data_text
        )
        print("Sample data insertion response (generator object):", data_response_gen)
        # list(data_response_gen) # Consume generator
    except Exception as e:
        print(f"Error during sample data insertion: {e}") # Consider logging
        # raise

# --- Define Admin Routes on admin_router ---
@admin_router.post("/products", response_model=List[Dict], tags=["Admin Products"])
async def add_product(
    product: ProductRequest,
    user: Dict[str, Any] = Depends(verify_admin)
):
    """Add a new product (admin only)"""
    product_text_message = f"""
    Add a new product with the following details:
    - Name: {product.name}
    - Price: {product.price}
    - Stock Quantity: {product.stock_quantity}
    - Description: {product.description or "N/A"}
    - Category: {product.category or "N/A"}
    - Image URL: {product.image_url or "N/A"}
    """
    request_session_id = str(uuid.uuid4())
    # await session_service.create_session(app_name='product', user_id=str(user["user_id"]), session_id=request_session_id) # If needed
    response_gen = product_runner.run(
        user_id=str(user["user_id"]),
        session_id=request_session_id,
        new_message=product_text_message
    )
    return process_run_response(response_gen)

@admin_router.put("/products/{product_id_path}", response_model=List[Dict], tags=["Admin Products"])
async def update_product(
    product_id_path: int, # Renamed to avoid clash with ProductUpdateRequest if it had product_id
    product: ProductUpdateRequest,
    user: Dict[str, Any] = Depends(verify_admin)
):
    """Update a product (admin only)"""
    update_fields = []
    if product.name is not None: update_fields.append(f"- Name: {product.name}")
    if product.price is not None: update_fields.append(f"- Price: {product.price}")
    if product.stock_quantity is not None: update_fields.append(f"- Stock Quantity: {product.stock_quantity}")
    if product.description is not None: update_fields.append(f"- Description: {product.description}")
    if product.category is not None: update_fields.append(f"- Category: {product.category}")
    if product.image_url is not None: update_fields.append(f"- Image URL: {product.image_url}")
    
    update_text_parts = "\n".join(update_fields)
    message_payload = f"Update product with ID {product_id_path} with the following changes:\n{update_text_parts}"
    request_session_id = str(uuid.uuid4())
    # await session_service.create_session(app_name='product', user_id=str(user["user_id"]), session_id=request_session_id) # If needed
    response_gen = product_runner.run(
        user_id=str(user["user_id"]),
        session_id=request_session_id,
        new_message=message_payload
    )
    return process_run_response(response_gen)

# --- Define Customer Routes on customer_router ---
@customer_router.get("/products", response_model=List[Dict], tags=["Customer Products"])
async def list_products(
    category: Optional[str] = None,
    #user: Dict[str, Any] = Depends(get_current_user)
):
    """List all products, optionally filtered by category"""
    message_text = f"Show me all products in the {category} category" if category else "Show me all available products"
    request_session_id = str(uuid.uuid4())
    # await session_service.create_session(app_name='product', user_id=str(user["user_id"]), session_id=request_session_id) # If needed
    response_gen = product_runner.run(
       user_id=str(user["user_id"]),
       session_id=request_session_id,
       new_message=message_text
    )
    return process_run_response(response_gen)

@customer_router.get("/cart", response_model=List[Dict], tags=["Customer Cart"])
async def view_cart(
    user: Dict[str, Any] = Depends(get_current_user)
):
    """View the current user's shopping cart"""
    message_text = "Show me my current shopping cart"
    request_session_id = str(uuid.uuid4())
    # await session_service.create_session(app_name='cart', user_id=str(user["user_id"]), session_id=request_session_id) # If needed
    response_gen = cart_runner.run(
        user_id=str(user["user_id"]),
        session_id=request_session_id,
        new_message=message_text
    )
    return process_run_response(response_gen)

# --- MOVED TO THE END: REGISTER ROUTERS WITH THE MAIN APP ---
# This must happen AFTER all routes are defined on admin_router and customer_router.
app.include_router(admin_router, prefix="/api/admin") # Tags are now defined on routes themselves
app.include_router(customer_router, prefix="/api/customer") # Tags are now defined on routes themselves

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)