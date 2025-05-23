import json
import logging
import re  # Import the re module for regular expressions
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

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
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.split(" ")[1]

        # Verify token using auth tools
        from tools.auth_tools import verify_jwt_token

        result = verify_jwt_token(token)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return result["user"]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def process_run_response(response_generator) -> Dict[str, Any]:
    """Process the response from agent runners and return structured data."""
    try:
        events = []
        all_parsed_json_responses = []
        
        # Regular expression to find JSON objects.
        # It looks for a '{' followed by any characters (non-greedy) until a '}'
        # This is more robust than splitting by '}{'
        json_pattern = re.compile(r'(\{.*?})')

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

                    # Attempt to parse JSON content from the agent
                    if hasattr(event, 'author') and event.author and event.author != "user":
                        content_stripped = content.strip()
                        # Remove markdown code block if present
                        if content_stripped.startswith('```json') and content_stripped.endswith('```'):
                            content_stripped = content_stripped[7:-3].strip()

                        # Use regex to find all JSON-like objects in the string
                        json_matches = json_pattern.findall(content_stripped)

                        for match in json_matches:
                            try:
                                # Replace Python boolean with JSON boolean and escape single quotes
                                json_candidate = match.replace("True", "true").replace("False", "false").replace("\\'", "'")
                                parsed_json = json.loads(json_candidate)
                                all_parsed_json_responses.append(parsed_json)
                                logger.info(f"Successfully parsed JSON object.")
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse JSON segment: {e} for content: {match[:100]}...")
                                # If a part fails, it's ok, continue to try others
                                pass

        logger.info(f"Processed {len(events)} events, {len(all_parsed_json_responses)} individual JSON results parsed.")

        # Create a structured response based on parsed JSONs
        if all_parsed_json_responses:
            if len(all_parsed_json_responses) == 1:
                # If only one JSON was parsed, return it directly under 'data'
                return {
                    "success": True,
                    "message": "Agent response processed successfully.",
                    "data": all_parsed_json_responses[0]
                }
            else:
                # If multiple JSONs were parsed, return them as a list under 'data'
                return {
                    "success": True,
                    "message": "Multiple agent responses processed successfully.",
                    "data": {"responses": all_parsed_json_responses} # Wrap multiple in a 'responses' key
                }
        elif events:
            # If no structured JSON was found, but there are events, return the last content as a raw message
            last_event = events[-1]
            return {
                "success": True,
                "message": last_event["content"],
                "data": {"raw_text_response": last_event["content"]} # Still provide raw for debugging/fallback
            }
        else:
            # No events at all
            return {
                "success": False,
                "message": "No response received from agent",
                "error": "Agent did not provide any response",
                "data": None
            }

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


@chat_router.post("/chat", tags=["Chat"])
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