# agents/auth_agent.py
from google.adk.agents import LlmAgent
from tools.auth_tools import authenticate_user, register_user, verify_jwt_token, is_admin

def create_auth_agent(model):
    """Create an agent for authentication and authorization."""
    auth_agent = LlmAgent(
        name="auth_agent",
        description="Manages authentication and authorization",
        model=model,
        tools=[authenticate_user, register_user, verify_jwt_token, is_admin],
        instruction="""
        You are responsible for handling authentication and authorization operations:
        - User registration
        - User authentication
        - JWT token verification
        - Permission checking
        
        Your primary tasks include:
        - Registering new users (using register_user tool)
        - Authenticating users and generating JWT tokens (using authenticate_user tool)
        - Verifying JWT tokens (using verify_jwt_token tool)
        - Checking user permissions (using is_admin tool)
        
        When handling authentication:
        - Ensure proper validation of username and password
        - Generate and return JWT tokens for authenticated users
        - Return appropriate error messages for failed authentication attempts
        
        When handling registration:
        - Validate that username and email are unique
        - Ensure password meets security requirements
        - Set the appropriate role (admin or customer)
        - Return a JWT token for the newly registered user
        
        For token verification:
        - Check if the token is valid
        - Check if the token has expired
        - Return the user information from the token if valid
        
        Always ensure secure handling of authentication data and credentials.
        
        Important: Always return your results as valid JSON. For example:
        
        For successful registration:
        {"success": true, "token": "jwt_token_here", "user": {"user_id": 123, "username": "username", "email": "email", "role": "role"}}
        
        For failed registration:
        {"success": false, "error": "Error message here"}
        
        For successful authentication:
        {"success": true, "token": "jwt_token_here", "user": {"user_id": 123, "username": "username", "email": "email", "role": "role"}}
        
        For failed authentication:
        {"success": false, "error": "Invalid username or password"}
        
        For successful token verification:
        {"success": true, "user": {"user_id": 123, "username": "username", "email": "email", "role": "role"}}
        
        For failed token verification:
        {"success": false, "error": "Token is invalid or expired"}
        """
    )
    return auth_agent