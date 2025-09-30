import shopify
import os
from datetime import datetime
from pyactiveresource.connection import UnauthorizedAccess


# --- SCRIPT LOGIC ---
def get_shopify_orders(shop_url, api_version, access_token, api_key):
    """
    Connects to the Shopify API and fetches the latest unfulfilled orders.
    """
    if not all([shop_url, api_version, api_key, access_token]):
        print("Error: Please set all required environment variables in your .env file.")
        return None
    
    found_orders = None

    try:
        # Create a Shopify session and activate it
        session = shopify.Session(shop_url, api_version, access_token)
        shopify.ShopifyResource.activate_session(session)

        print("Successfully connected to Shopify API.")
        print("-" * 30)

        # Fetch the latest 10 orders that are unfulfilled.
        orders = shopify.Order.find(fulfillment_status='unfulfilled', limit=10)

        if not orders:
            print("No unfulfilled orders found.")
            return

        print(f"Found {len(orders)} recent unfulfilled orders. Displaying details:")
        print("-" * 30)

        found_orders = orders

    except UnauthorizedAccess as e:
        print(f"Authentication Error: {e}")
        print("Please check your Shopify API key, access token, and shop URL in the .env file.")
        print("The provided credentials are not valid.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Always clear the session after use
        shopify.ShopifyResource.clear_session()
        return found_orders


def pretty_print_orders(orders):
    # Iterate through the orders and print key details
    for order in orders:
        print(type(order))
        order_number = order.name
        created_at = datetime.fromisoformat(order.created_at.replace("Z", "+00:00"))
        customer_name = "N/A"
        if order.customer:
            customer_name = f"{order.customer.first_name} {order.customer.last_name}"

        total_price = order.total_price
        
        print(f"Order #{order_number}")
        print(f"  Customer: {customer_name}")
        print(f"  Date: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Total Price: ${total_price}")

        # Iterate through each line item
        print("  Line Items:")
        for item in order.line_items:
            print(f"    - {item.quantity} x {item.title}")

            # Check for and print custom properties like color or type
            if hasattr(item, 'properties') and item.properties:
                print("      Properties:")
                for prop in item.properties:
                    print(f"        - {prop.name}: {prop.value}")
            
            print(f"      Price: ${item.price}")
        
        print("-" * 30)
