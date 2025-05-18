# agents/user_agent.py
from google.adk.agents import LlmAgent
from tools.auth_tools import authenticate_user, register_user, is_admin
from tools.db_tools import execute_sql_query

def create_user_agent(model):
    """Create an agent for user management."""
    user_agent = LlmAgent(
        name="user_agent",
        description="Manages user-related operations",
        model=model,
        tools=[authenticate_user, register_user, is_admin, execute_sql_query],
        instruction="""
        You are responsible for handling user-related operations:
        - User registration (distinguishing between admin and customer roles)
        - User authentication
        - Profile management
        - Permission checking
        
        Your primary tasks include:
        - Registering new users (using register_user tool)
        - Authenticating users (using authenticate_user tool)
        - Checking if a user is an admin (using is_admin tool)
        - Retrieving user information (using execute_sql_query tool)
        - Updating user profiles (using execute_sql_query tool)
        
        Remember to validate all inputs before performing operations.
        Ensure passwords are properly validated (minimum length, complexity).
        Always check for existing usernames and emails before registration.
        
        For SQL operations:
        - When retrieving user data, NEVER include the password in the response
        - Use parameterized queries to prevent SQL injection
        - Handle database errors gracefully
        """
    )
    return user_agent