# api/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Import from api.app
from api.app import verify_admin

# Initialize the router
admin_router = APIRouter()

# Define request models
class ProductRequest(BaseModel):
    name: str
    price: float
    stock_quantity: int
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

class ProductUpdateRequest(BaseModel):
    product_id: int
    name: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None

class OrderStatusUpdateRequest(BaseModel):
    order_id: int
    status: str

class MessageRequest(BaseModel):
    message: str

# Note: The endpoints will be defined in main.py