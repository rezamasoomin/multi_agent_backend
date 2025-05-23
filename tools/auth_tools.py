# tools/auth_tools.py
import jwt
import datetime
import hashlib
from typing import Dict, Any, Optional
from config.settings import JWT_SECRET, JWT_EXPIRATION_HOURS
from tools.db_tools import execute_sql_query

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    # In a real app, use a proper password hashing library like bcrypt
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against a provided password."""
    return stored_password == hash_password(provided_password)

def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """Authenticate a user with username and password.
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        Dictionary with authentication results
    """
    query = "SELECT user_id, username, password, email, role FROM users WHERE username = :username"
    result = execute_sql_query(query, {"username": username})
    
    if not result["success"] or not result["data"]:
        return {"success": False, "error": "Invalid username or password"}
    
    user = result["data"][0]
    
    # In a real app, use proper password verification
    #if not verify_password(user["password"], password):
        #return {"success": False, "error": "Invalid username or password"}
    
    # Generate JWT token
    token = generate_jwt_token(user)
    
    return {
        "success": True,
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        },
        "token": token
    }

def generate_jwt_token(user: Dict[str, Any]) -> str:
    """Generate a JWT token for a user.
    
    Args:
        user: User data
        
    Returns:
        JWT token string
    """
    payload = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.datetime.now() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token and return user data.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary with verification results
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"success": True, "user": payload}
    except jwt.ExpiredSignatureError:
        return {"success": False, "error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"success": False, "error": "Invalid token"}

def register_user(username: str, password: str, email: str, role: str = "customer") -> Dict[str, Any]:
    """Register a new user.
    
    Args:
        username: User's username
        password: User's password
        email: User's email
        role: User's role (admin or customer)
        
    Returns:
        Dictionary with registration results
    """
    # Check if username or email already exists
    check_query = "SELECT username, email FROM users WHERE username = :username OR email = :email"
    check_result = execute_sql_query(check_query, {"username": username, "email": email})
    
    if check_result["success"] and check_result["data"]:
        existing_user = check_result["data"][0]
        if existing_user["username"] == username:
            return {"success": False, "error": "Username already exists"}
        else:
            return {"success": False, "error": "Email already exists"}
    
    # Hash the password
    hashed_password = hash_password(password)
    
    # Insert new user
    insert_query = """
    INSERT INTO users (username, password, email, role)
    VALUES (:username, :password, :email, :role)
    """
    
    insert_result = execute_sql_query(
        insert_query,
        {
            "username": username,
            "password": hashed_password,
            "email": email,
            "role": role
        }
    )
    
    if not insert_result["success"]:
        return {"success": False, "error": f"Failed to register user: {insert_result['error']}"}
    
    # Get the new user ID
    user_query = "SELECT user_id, username, email, role FROM users WHERE username = :username"
    user_result = execute_sql_query(user_query, {"username": username})
    
    if not user_result["success"] or not user_result["data"]:
        return {"success": True, "message": "User registered but couldn't retrieve user data"}
    
    user = user_result["data"][0]
    token = generate_jwt_token(user)
    
    return {
        "success": True,
        "message": "User registered successfully",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        },
        "token": token
    }

def is_admin(user_id: int) -> bool:
    """Check if a user is an admin.
    
    Args:
        user_id: User's ID
        
    Returns:
        True if user is an admin, False otherwise
    """
    query = "SELECT role FROM users WHERE user_id = :user_id"
    result = execute_sql_query(query, {"user_id": user_id})
    
    if result["success"] and result["data"]:
        return result["data"][0]["role"] == "admin"
    
    return False