# agents/schema_agent.py
from google.adk.agents import LlmAgent
from tools.db_tools import create_database_schema, insert_sample_data

def create_schema_agent(model):
    """Create an agent for database schema management."""
    schema_agent = LlmAgent(
        name="schema_agent",
        description="Creates and manages database schema for the e-commerce application",
        model=model,
        tools=[create_database_schema, insert_sample_data],
        instruction="""
        You are responsible for creating and managing the database schema for an e-commerce application.
        You need to create tables for users, products, cart items, orders, and order items.
        
        The schema includes these tables:
        1. users - Stores user accounts (both admins and customers)
        2. products - Stores product information
        3. cart_items - Stores items in users' shopping carts
        4. orders - Stores order information
        5. order_items - Stores items within orders
        
        Your primary tasks include:
        - Creating the initial database schema
        - Adding sample data for testing
        - Handling schema migrations when needed
        
        You can use the create_database_schema() tool to set up the initial schema
        and the insert_sample_data() tool to add test data.
        """
    )
    return schema_agent