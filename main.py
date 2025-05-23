import os
import uuid
import google.generativeai as genai
import uvicorn
from fastapi import Depends
from pydantic import BaseModel
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
from agents.auth_agent import create_auth_agent
from agents.orchestrator_agent import create_orchestrator_agent

# Import the main 'app' instance
from api.app import app

# Import the routers
from api.auth_routes import auth_router, set_auth_dependencies
from api.chat_routes import chat_router, set_chat_dependencies

# Initialize Google Gemini
genai.configure(api_key=GOOGLE_API_KEY) 
model = 'gemini-2.0-flash'

# Initialize database session service
session_service = DatabaseSessionService(db_url=DATABASE_URL)

# Initialize database and sample data
from tools.db_tools import create_database_schema, insert_sample_data
print("Creating database schema...")
schema_result = create_database_schema()
print(f"Schema creation result: {schema_result}")

print("Inserting sample data...")
sample_data_result = insert_sample_data()
print(f"Sample data insertion result: {sample_data_result}")

# Initialize agents
schema_agent = create_schema_agent(model)
auth_agent = create_auth_agent(model)

# Create orchestrator that handles all e-commerce operations
orchestrator_agent = create_orchestrator_agent(model)

# Initialize runners
schema_runner = Runner(agent=schema_agent, app_name='schema', session_service=session_service)
orchestrator_runner = Runner(agent=orchestrator_agent, app_name='orchestrator', session_service=session_service)
auth_runner = Runner(agent=auth_agent, app_name='auth', session_service=session_service)

# Set dependencies for auth routes
set_auth_dependencies(auth_runner, session_service)

# Set dependencies for chat routes
set_chat_dependencies(orchestrator_runner, session_service)

# Helper to process runner generator (kept for backward compatibility if needed)
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
    
    # Initialize schema
    schema_message_text = "Initialize the database schema for our e-commerce application"
    print(f"Initializing schema with user_id: {SYSTEM_USER_ID}, session_id: {session_id_for_init}")
    try:
        schema_response_gen = schema_runner.run(
            user_id=SYSTEM_USER_ID,
            session_id=session_id_for_init,
            new_message=schema_message_text
        )
        print("Schema creation response (generator object):", schema_response_gen)
    except Exception as e:
        print(f"Error during schema initialization: {e}")

    # Insert sample data
    sample_data_text = "Insert sample data for testing our e-commerce application"
    print(f"Inserting sample data with user_id: {SYSTEM_USER_ID}, session_id: {session_id_for_init}")
    try:
        data_response_gen = schema_runner.run(
            user_id=SYSTEM_USER_ID,
            session_id=session_id_for_init,
            new_message=sample_data_text
        )
        print("Sample data insertion response (generator object):", data_response_gen)
    except Exception as e:
        print(f"Error during sample data insertion: {e}")

# Register routers with the main app
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])

# Add a root endpoint for API info
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Multi-Agent E-commerce Chat API",
        "version": "1.0.0",
        "endpoints": {
            "authentication": "/api/auth/",
            "chat": "/api/chat",
            "documentation": "/docs",
            "health": "/api/chat/health"
        },
        "usage": {
            "login": "POST /api/auth/token with username and password",
            "register": "POST /api/auth/register with user details",
            "chat": "POST /api/chat with Authorization header and message",
            "example_message": "I want to see all black T-shirts"
        }
    }

# Add a simple health check
@app.get("/health", tags=["System"])
async def health_check():
    """System health check."""
    return {
        "status": "healthy",
        "database": "connected" if session_service else "disconnected",
        "agents": {
            "orchestrator": orchestrator_runner is not None,
            "auth": auth_runner is not None,
            "schema": schema_runner is not None
        }
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)