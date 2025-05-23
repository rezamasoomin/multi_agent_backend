# api/chat_routes.py
from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

chat_router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Optional session for conversation continuity

class ChatResponse(BaseModel):
    response: Dict[str, Any]
    session_id: str
    agent_used: str
    success: bool

# Global variables to hold references (will be set from main.py)
orchestrator_runner = None
session_service = None

def set_chat_dependencies(_orchestrator_runner, _session_service):
    """Set the dependencies needed for chat functionality."""
    global orchestrator_runner, session_service
    orchestrator_runner = _orchestrator_runner
    session_service = _session_service

def get_current_user_from_token(authorization: str = Header(None)) -> Dict[str, Any]:
    """Extract and verify user from Authorization header token."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = authorization.split(" ")[1]
        
        # Verify token using auth tools
        from tools.auth_tools import verify_jwt_token
        
        result = verify_jwt_token(token)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return result["user"]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

def process_run_response(response_generator) -> Dict[str, Any]:
    """Process the response from agent runners and return structured data."""
    try:
        events = []
        final_result = None
        
        # Consume the generator completely
        for event in response_generator:
            logger.info(f"Processing event: {type(event).__name__} from {getattr(event, 'author', 'unknown')}")
            
            if hasattr(event, 'content') and event.content:
                content = ""
                if hasattr(event.content, 'parts') and event.content.parts:
                    text_parts = []
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        content = " ".join(text_parts)
                elif hasattr(event.content, 'text') and event.content.text:
                    content = event.content.text
                else:
                    content = str(event.content)
                
                # Only add events with actual content
                if content and content.strip():
                    events.append({
                        "author": getattr(event, 'author', 'unknown'),
                        "content": content,
                        "timestamp": getattr(event, 'timestamp', None)
                    })
                    
                    logger.info(f"Event content: {content[:200]}...")
                    
                    # Try to parse as JSON if it's from the agent
                    if hasattr(event, 'author') and event.author and event.author != "user":
                        try:
                            content_stripped = content.strip()
                            if content_stripped.startswith('{') and content_stripped.endswith('}'):
                                final_result = json.loads(content_stripped)
                                logger.info("Successfully parsed JSON from agent response")
                        except json.JSONDecodeError:
                            # Not JSON, that's fine - use the text content
                            pass
        
        logger.info(f"Processed {len(events)} events, final_result: {final_result is not None}")
        
        # Create a structured response
        if final_result is None:
            if events:
                # Use the last event's content as the response
                last_event = events[-1]
                final_result = {
                    "success": True,
                    "message": json.loads(last_event["content"].replace("True", "true").replace("\\'", "'").strip()),
                    #"data": {"response": last_event["content"]},
                    #"raw_events": events
                }
            else:
                final_result = {
                    "success": False,
                    "message": "No response received from agent",
                    "error": "Agent did not provide any response",
                    "data": None
                }
        
        return final_result
    
    except Exception as e:
        logger.error(f"Error processing agent response: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Error processing response: {str(e)}",
            "message": "Failed to process agent response",
            "data": None
        }

def determine_agent_and_runner(message: str, user: Dict[str, Any]) -> tuple:
    """Always return the orchestrator - it will handle delegation internally."""
    return "orchestrator", orchestrator_runner

@chat_router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(
    chat_request: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """Main chat endpoint that uses orchestrator agent for intelligent delegation."""
    
    if not orchestrator_runner:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat system not initialized"
        )
    
    try:
        # Generate or use provided session ID
        request_session_id = chat_request.session_id or str(uuid.uuid4())
        
        # Always use orchestrator - it will decide internally
        agent_name, runner = determine_agent_and_runner(chat_request.message, user)
        
        # Create session if it doesn't exist
        try:
            await session_service.create_session(
                app_name=agent_name,
                user_id=str(user["user_id"]),
                session_id=request_session_id
            )
            logger.info(f"Created session {request_session_id} for user {user['username']} with {agent_name}")
        except Exception as session_error:
            # Session might already exist, which is fine
            logger.info(f"Session creation note: {str(session_error)}")
        
        # Create the proper Content object for ADK with user context
        from google.genai import types
        
        # Include user context in the message for the agent
        user_context_message = f"User ID: {user['user_id']}, Username: {user['username']}, Role: {user['role']}\nRequest: {chat_request.message}"
        
        content = types.Content(
            role='user', 
            parts=[types.Part(text=user_context_message)]
        )
        
        # Run the orchestrator agent
        logger.info(f"Processing message with {agent_name} for user {user['username']}")
        
        response_gen = runner.run(
            user_id=str(user["user_id"]),
            session_id=request_session_id,
            new_message=content
        )
        
        # Process the response
        result = process_run_response(response_gen)
        
        return ChatResponse(
            response=result,
            session_id=request_session_id,
            agent_used=agent_name,
            success=result.get("success", True)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )

@chat_router.post("/chat/direct", response_model=Dict[str, Any], tags=["Chat"])
async def direct_chat_endpoint(
    chat_request: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """Direct chat endpoint that uses tools directly without ADK runners for testing."""
    
    try:
        message_lower = chat_request.message.lower()
        
        # Handle product requests directly
        if any(keyword in message_lower for keyword in ["product", "t-shirt", "shirt", "show", "list"]):
            from tools.db_tools import execute_sql_query
            
            # Build query based on the message
            if "t-shirt" in message_lower or "shirt" in message_lower:
                query = """
                SELECT product_id, name, description, price, stock_quantity, category, image_url
                FROM products 
                WHERE (name LIKE '%shirt%' OR name LIKE '%t-shirt%' OR description LIKE '%shirt%') 
                AND stock_quantity > 0
                """
            elif "black" in message_lower:
                query = """
                SELECT product_id, name, description, price, stock_quantity, category, image_url
                FROM products 
                WHERE (name LIKE '%black%' OR description LIKE '%black%') 
                AND stock_quantity > 0
                """
            else:
                query = """
                SELECT product_id, name, description, price, stock_quantity, category, image_url
                FROM products 
                WHERE stock_quantity > 0
                ORDER BY created_at DESC
                """
            
            result = execute_sql_query(query)
            
            if result.get("success"):
                return {
                    "success": True,
                    "data": result.get("data", []),
                    "message": f"Found {len(result.get('data', []))} products matching your request",
                    "query_executed": query
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Database query failed"),
                    "message": "Failed to retrieve products"
                }
        
        # Handle cart requests
        elif any(keyword in message_lower for keyword in ["cart", "shopping"]):
            from tools.db_tools import execute_sql_query
            
            query = """
            SELECT ci.cart_id, ci.quantity, ci.added_at,
                   p.product_id, p.name, p.price, p.description,
                   (ci.quantity * p.price) as total_price
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.product_id
            WHERE ci.user_id = :user_id
            ORDER BY ci.added_at DESC
            """
            
            result = execute_sql_query(query, {"user_id": user["user_id"]})
            
            if result.get("success"):
                cart_items = result.get("data", [])
                total_amount = sum(item.get("total_price", 0) for item in cart_items)
                
                return {
                    "success": True,
                    "data": {
                        "cart_items": cart_items,
                        "total_amount": total_amount,
                        "item_count": len(cart_items)
                    },
                    "message": f"Your cart contains {len(cart_items)} items with total amount ${total_amount:.2f}"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Database query failed"),
                    "message": "Failed to retrieve cart items"
                }
        
        else:
            return {
                "success": True,
                "message": "I can help you with products, cart, and orders. Try asking 'show me products' or 'show my cart'",
                "data": {
                    "available_commands": [
                        "show me products",
                        "show me t-shirts", 
                        "show my cart",
                        "show my orders"
                    ]
                }
            }
    
    except Exception as e:
        logger.error(f"Direct chat error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "message": "An error occurred while processing your request"
        }

@chat_router.get("/debug/products", tags=["Debug"])
async def debug_products():
    """Debug endpoint to test database connectivity."""
    try:
        from tools.db_tools import execute_sql_query
        
        result = execute_sql_query("SELECT * FROM products LIMIT 5")
        return {
            "database_query_result": result,
            "status": "success" if result.get("success") else "error"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

@chat_router.get("/debug/users", tags=["Debug"])
async def debug_users():
    """Debug endpoint to check users table."""
    try:
        from tools.db_tools import execute_sql_query
        
        result = execute_sql_query("SELECT user_id, username, email, role FROM users")
        return {
            "database_query_result": result,
            "status": "success" if result.get("success") else "error"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }