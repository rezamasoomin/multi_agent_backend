# api/customer_routes.py
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Import from api.app
from api.app import get_current_user

# Initialize the router
customer_router = APIRouter()

# Define request models
class CartItemRequest(BaseModel):
    product_id: int
    quantity: int

class MessageRequest(BaseModel):
    message: str

# Note: The endpoints will be defined in main.py