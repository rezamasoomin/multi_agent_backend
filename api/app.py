from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Example if you use token auth
from typing import Dict, Any

app = FastAPI(
    title="Multi-Agent E-commerce API",
    description="API for managing an e-commerce platform with multiple agents.",
    version="1.0.0"
)

# --- Authentication Utilities (Example Stubs) ---
# Replace these with your actual authentication logic.
# If complex, these might live in a separate auth.py and be imported here.

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token") # Example token URL


@app.get("/", tags=["General"])
async def root():
    """
    Root endpoint for the API.
    """
    return {"message": "Welcome to the Multi-Agent E-commerce API"}

@app.get("/api/health", tags=["General"])
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Retrieves the current user based on the provided token.
    """
    from tools.auth_tools import verify_jwt_token
    
    result = verify_jwt_token(token)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["error"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return result["user"]

async def verify_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Verifies if the current user has admin privileges.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges"
        )
    return current_user
# IMPORTANT: Do NOT call app.include_router for admin_router or customer_router here.
# That will be handled in main.py after routes are defined on those routers.