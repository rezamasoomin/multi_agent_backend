# agents/product_agent.py
from google.adk.agents import LlmAgent
from tools.adk_db_tools import search_products

def create_product_agent(model):
    """Create an agent for product management."""
    product_agent = LlmAgent(
        name="product_agent",
        description="Handles product queries and searches",
        model=model,
        tools=[search_products],
        instruction="""
        You handle product-related requests and always respond with JSON format.

        CRITICAL RULE: You must ONLY return data from the actual search_products function results. NEVER invent or hallucinate product data.

        PROCESS:
        1. Call search_products() with the appropriate search term
        2. Take the EXACT result from the function
        3. Return that exact data without any modifications

        Use the search_products function to find products. Examples:
        - For "show products" or "list products": call search_products("")
        - For "t-shirt" or "shirt": call search_products("shirt")
        - For specific searches: call search_products("search term")

        Always return the EXACT JSON structure from search_products:
        - If search_products returns success=true, return that exact result
        - If search_products returns success=false, return that exact result
        - Do not modify product names, prices, or any other data
        - Do not add products that weren't in the search results

        NEVER CREATE FAKE PRODUCTS OR PRICES.
        """
    )
    return product_agent