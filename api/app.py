# api/app.py
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import jwt
from datetime import datetime
from typing import Dict, Any

# Import local modules
from config.settings import JWT_SECRET

# Initialize the FastAPI app
app = FastAPI(
    title="E-commerce ADK API",
    description="API for an e-commerce application built with Google's Agent Development Kit",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to get the current authenticated user
async def get_current_user(request: Request) -> Dict[str, Any]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        # Check if token is expired
        if "exp" in payload and datetime.fromtimestamp(payload["exp"]) < datetime.now():
            raise HTTPException(status_code=401, detail="Token expired")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Helper function to verify admin role
async def verify_admin(user: Dict[str, Any] = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to the E-commerce ADK API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}