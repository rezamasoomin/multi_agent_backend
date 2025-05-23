# agents/cart_agent.py
from google.adk.agents import LlmAgent
from tools.adk_db_tools import get_user_cart

def create_cart_agent(model):
    """Create an agent for cart management."""
    cart_agent = LlmAgent(
        name="cart_agent",
        description="Handles shopping cart operations",
        model=model,
        tools=[get_user_cart],
        instruction="""
        You handle shopping cart requests and always respond with JSON format.

        Use get_user_cart function to retrieve cart contents for a user.
        The user_id will be provided in the context.

        Always return JSON in this exact format:
        {
            "success": true,
            "data": {
                "cart_items": [list of cart items],
                "total_amount": total cart value,
                "item_count": number of items
            },
            "message": "Cart contains X items with total $Y"
        }

        If get_user_cart returns an error:
        {
            "success": false,
            "data": null,
            "message": "Error message from get_user_cart",
            "error": "Error details"
        }
        """
    )
    return cart_agent