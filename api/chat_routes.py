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
main_runner = None
auth_runner = None
product_runner = None
cart_runner = None
order_runner = None
user_runner = None
session_service = None

def set_chat_dependencies(_main_runner, _auth_runner, _product_runner, _cart_runner, 
                         _order_runner, _user_runner, _session_service):
    """Set the dependencies needed for chat functionality."""
    global main_runner, auth_runner, product_runner, cart_runner, order_runner, user_runner, session_service
    main_runner = _main_runner
    auth_runner = _auth_runner
    product_runner = _product_runner
    cart_runner = _cart_runner
    order_runner = _order_runner
    user_runner = _user_runner
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
                    text_parts = [part.text for part in event.content.parts if hasattr(part, 'text')]
                    content = " ".join(text_parts)
                elif hasattr(event.content, 'text'):
                    content = event.content.text
                else:
                    content = str(event.content)
                
                if content.strip():  # Only add non-empty content
                    events.append({
                        "author": getattr(event, 'author', 'unknown'),
                        "content": content,
                        "timestamp": getattr(event, 'timestamp', None)
                    })
                    
                    logger.info(f"Event content: {content[:200]}...")  # Log first 200 chars
                    
                    # Try to parse the last agent response as JSON for structured data
                    if hasattr(event, 'author') and event.author and event.author != "user":
                        try:
                            # Try to extract JSON from the content
                            content_stripped = content.strip()
                            if content_stripped.startswith('{') and content_stripped.endswith('}'):
                                final_result = json.loads(content_stripped)
                                logger.info("Successfully parsed JSON from agent response")
                            elif '"success"' in content and ('"data"' in content or '"message"' in content):
                                # Try to find JSON within the text
                                import re
                                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                                if json_match:
                                    final_result = json.loads(json_match.group())
                                    logger.info("Successfully extracted JSON from agent response")
                        except json.JSONDecodeError as je:
                            logger.warning(f"Failed to parse JSON from agent response: {je}")
                            pass
        
        logger.info(f"Processed {len(events)} events, final_result: {final_result is not None}")
        
        # If we couldn't extract structured JSON, create a structured response from the events
        if final_result is None:
            if events:
                # Try to create a meaningful response from the last event
                last_event = events[-1]
                final_result = {
                    "success": True,
                    "message": "Request processed successfully",
                    "data": last_event["content"],
                    "raw_events": events
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
    """Determine which agent should handle the message based on content and user role."""
    message_lower = message.lower()
    
    # Admin-specific operations
    if user.get("role") == "admin":
        if any(keyword in message_lower for keyword in ["add product", "create product", "new product"]):
            return "product", product_runner
        elif any(keyword in message_lower for keyword in ["update product", "edit product", "modify product"]):
            return "product", product_runner
        elif any(keyword in message_lower for keyword in ["delete product", "remove product"]):
            return "product", product_runner
        elif any(keyword in message_lower for keyword in ["all orders", "manage orders", "order status"]):
            return "order", order_runner
        elif any(keyword in message_lower for keyword in ["all users", "manage users", "user list"]):
            return "user", user_runner
    
    # Product-related queries (both admin and customer)
    if any(keyword in message_lower for keyword in ["product", "list", "show", "search", "find", "catalog"]):
        return "product", product_runner
    
    # Cart-related queries
    elif any(keyword in message_lower for keyword in ["cart", "add to cart", "remove from cart", "shopping"]):
        return "cart", cart_runner
    
    # Order-related queries
    elif any(keyword in message_lower for keyword in ["order", "purchase", "buy", "checkout", "my orders"]):
        return "order", order_runner
    
    # User profile queries
    elif any(keyword in message_lower for keyword in ["profile", "account", "my info", "update profile"]):
        return "user", user_runner
    
    # Default to main agent for general queries
    else:
        return "main", main_runner

@chat_router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(
    chat_request: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """Main chat endpoint that routes messages to appropriate agents."""
    
    if not main_runner:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat system not initialized"
        )
    
    try:
        # Generate or use provided session ID
        request_session_id = chat_request.session_id or str(uuid.uuid4())
        
        # Determine which agent should handle this message
        agent_name, runner = determine_agent_and_runner(chat_request.message, user)
        
        # Create session if it doesn't exist
        try:
            await session_service.create_session(
                app_name=agent_name,
                user_id=str(user["user_id"]),
                session_id=request_session_id
            )
            logger.info(f"Created session {request_session_id} for user {user['username']} with {agent_name} agent")
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
        
        # Run the appropriate agent
        logger.info(f"Processing message with {agent_name} agent for user {user['username']}")
        
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