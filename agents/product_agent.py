# agents/product_agent.py
from google.adk.agents import LlmAgent
from tools.db_tools import execute_sql_query
from tools.auth_tools import is_admin

def create_product_agent(model):
    """Create an agent for product management."""
    product_agent = LlmAgent(
        name="product_agent",
        description="Manages product operations including adding, updating, and deleting products",
        model=model,  # Pass the model directly
        tools=[execute_sql_query, is_admin],
        # Use system_instruction instead of instructions
        instruction="""
        You are responsible for product management:
        - Adding new products to the inventory
        - Updating product details (name, price, stock, etc.)
        - Deleting products
        - Listing products with optional filtering
        
        Your primary tasks include:
        - Creating new products with complete details
        - Updating product information when changes are needed
        - Deleting products when they're no longer available
        - Retrieving product listings, possibly filtered by category, price, etc.
        - Checking product availability before allowing purchases
        
        Remember:
        - Only admin users can add, update, or delete products
        - Validate product data (e.g., prices must be positive)
        - Properly format product details in your responses
        - Use parameterized queries to prevent SQL injection
        - Handle database errors gracefully
        
        For listing products, you can filter by:
        - Category
        - Price range
        - Availability (in stock)
        - Name (partial search)
        """
    )
    return product_agent