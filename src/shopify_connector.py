import shopify
import os
from datetime import datetime
from pyactiveresource.connection import UnauthorizedAccess
import yaml 
from dataclasses import dataclass
from typing import List, Optional
    

def order_to_dict(order) -> dict:
    """
    Convert a Shopify order object to a dictionary for easier processing.
    
    Args:
        order: A Shopify order object
    
    Returns:
        dict: Order data in dictionary format with nested structures
    """
    # Base order information
    order_dict = {
        'id': getattr(order, 'id', None),
        'name': getattr(order, 'name', ''),
        'created_at': getattr(order, 'created_at', ''),
        'total_price': getattr(order, 'total_price', 0.0),
        'note': getattr(order, 'note', ''),
        'customer': {
            'name': getattr(order.customer, 'name', '') if hasattr(order, 'customer') else '',
            'email': getattr(order.customer, 'email', '') if hasattr(order, 'customer') else ''
        },
        'line_items': []
    }
    
    # Process line items
    for item in getattr(order, 'line_items', []):
        item_dict = {
            'id': getattr(item, 'id', None),
            'title': getattr(item, 'title', ''),
            'quantity': getattr(item, 'quantity', 0),
            'price': getattr(item, 'price', 0.0),
            'properties': {}
        }
        
        # Convert properties to a simple key-value dict
        for prop in getattr(item, 'properties', []):
            prop_name = getattr(prop, 'name', '')
            prop_value = getattr(prop, 'value', '')
            if prop_name:
                item_dict['properties'][prop_name] = prop_value
                
        order_dict['line_items'].append(item_dict)
    
    return order_dict


# --- SCRIPT LOGIC ---
def get_shopify_orders(shop_url, api_version, access_token, api_key) -> Optional[List[dict]]:
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

        found_orders = [order_to_dict(o) for o in orders]

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

def save_orders_as_yaml(orders, output_dir: str = 'test_data'):
    """
    Save Shopify orders as YAML files for testing purposes.
    
    Args:
        orders: List of Shopify order objects
        output_dir: Directory to save the YAML files
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for order in orders:
        order_dict = order_to_dict(order)

        # Create filename with timestamp and order number
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"order_{order.name}_{timestamp}.yaml"
        filepath = os.path.join(output_dir, filename)

        # Save as YAML
        with open(filepath, 'w') as f:
            yaml.dump(order_dict, f, default_flow_style=False, sort_keys=False)
