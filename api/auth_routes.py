from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
import json
import asyncio
from uuid import uuid4
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_router = APIRouter()

class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: str
    role: Optional[str] = "customer"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

# Global variables to hold references
auth_agent = None
session_service = None
schema_initialized = False

def set_auth_dependencies(_auth_agent, _session_service):
    global auth_agent, session_service
    auth_agent = _auth_agent
    session_service = _session_service

# Helper function to ensure database schema is created
def ensure_schema_exists():
    global schema_initialized
    if not schema_initialized:
        try:
            # Import the DB schema creation tool
            from tools.db_tools import create_database_schema
            
            # Create the schema if it doesn't exist
            result = create_database_schema()
            logger.info(f"Database schema creation result: {result}")
            
            # Mark schema as initialized
            schema_initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to create database schema: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    return True

@auth_router.post("/register", response_model=TokenResponse, tags=["Authentication"])
async def register_endpoint(user_data: UserRegisterRequest):
    """Register a new user."""
    if not auth_agent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication agent not initialized"
        )
    
    # Ensure database schema exists
    if not ensure_schema_exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize database schema"
        )
    
    try:
        # Import the necessary auth tools
        from tools.auth_tools import register_user, authenticate_user
        
        # Step 1: Register the user
        register_result = register_user(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email,
            role=user_data.role
        )
        
        if not register_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=register_result.get("error", "Registration failed")
            )
        
        # Step 2: Now authenticate the newly registered user to get the token
        auth_result = authenticate_user(
            username=user_data.username,
            password=user_data.password
        )
        
        if not auth_result.get("success"):
            # This should not happen, but just in case
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User registered successfully, but authentication failed"
            )
            
        # Return the token response
        return {
            "access_token": auth_result["token"],
            "token_type": "bearer",
            "user": auth_result["user"]
        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during registration: {str(e)}"
        )

@auth_router.post("/token", response_model=TokenResponse, tags=["Authentication"])
async def login_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a user and return a token."""
    if not auth_agent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication agent not initialized"
        )
    
    # Ensure database schema exists
    if not ensure_schema_exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize database schema"
        )
    
    try:
        # Use the auth tools directly instead of through the agent
        from tools.auth_tools import authenticate_user
        
        # Call the authenticate_user function directly
        result = authenticate_user(
            username=form_data.username,
            password=form_data.password
        )
        
        logger.info(f"Authentication result: {result}")
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if "token" not in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication successful but no token was generated"
            )
            
        return {
            "access_token": result["token"],
            "token_type": "bearer",
            "user": result["user"]
        }
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during authentication: {str(e)}"
        )

@auth_router.get("/verify", tags=["Authentication"])
async def verify_token_endpoint(token: str):
    """Verify a JWT token."""
    if not auth_agent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication agent not initialized"
        )
    
    try:
        # Use the auth tools directly instead of through the agent
        from tools.auth_tools import verify_jwt_token
        
        # Call the verify_jwt_token function directly
        result = verify_jwt_token(token)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get("error", "Invalid token")
            )
            
        return result
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during token verification: {str(e)}"
        )

# Add a health check endpoint to verify schema initialization
@auth_router.get("/health", tags=["System"])
async def health_check():
    """Check if the auth system is healthy and database schema is initialized."""
    schema_ok = ensure_schema_exists()
    return {
        "status": "healthy" if schema_ok else "unhealthy",
        "schema_initialized": schema_initialized,
        "auth_agent_ready": auth_agent is not None,
        "session_service_ready": session_service is not None
    }