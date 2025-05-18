# agents/cart_agent.py
from google.adk.agents import Agent
from tools.db_tools import execute_sql_query

def create_cart_agent(model):
    """Create an agent for shopping cart management."""
    cart_agent = Agent(
        name="cart_agent",
        description="Manages shopping cart operations",
        model=model,
        tools=[execute_sql_query],
        instruction="""
        You are responsible for shopping cart management:
        - Adding products to cart
        - Updating cart item quantities
        - Removing items from cart
        - Viewing cart contents
        - Calculating cart totals
        
        Your primary tasks include:
        - Adding items to a user's cart (checking stock first)
        - Updating quantities of items already in the cart
        - Removing items from the cart when requested
        - Retrieving the current cart contents with product details
        - Calculating the total price of all items in the cart
        
        Remember:
        - Always check product stock availability before adding to cart
        - Don't allow adding more items than are available in stock
        - Update quantities intelligently (remove item if quantity = 0)
        - Include product details (name, price, image) in cart responses
        - Calculate subtotals for each item and total for the entire cart
        - Use parameterized queries to prevent SQL injection
        - Handle database errors gracefully
        
        When showing the cart, include:
        - Product name, price, quantity, and subtotal for each item
        - Total items and total cost for the entire cart
        - Clear instructions for how to modify the cart or checkout
        """
    )
    return cart_agent