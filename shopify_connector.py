import shopify
import os
from datetime import datetime
from pyactiveresource.connection import UnauthorizedAccess
import yaml
from types import SimpleNamespace
from typing import List

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
        # Convert order to dictionary
        order_dict = {
            'id': order.id,
            'name': order.name,
            'created_at': order.created_at,
            'line_items': []
        }

        # Extract line items
        for item in order.line_items:
            item_dict = {
                'title': item['title'],
                'quantity': item['quantity'],
                'properties': []
            }
            
            if hasattr(item, 'properties'):
                for prop in item['properties']:
                    item_dict['properties'].append({
                        'name': prop.name,
                        'value': prop.value
                    })
            
            order_dict['line_items'].append(item_dict)

        # Create filename with timestamp and order number
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"order_{order.name}_{timestamp}.yaml"
        filepath = os.path.join(output_dir, filename)

        # Save as YAML
        with open(filepath, 'w') as f:
            yaml.dump(order_dict, f, default_flow_style=False, sort_keys=False)

def load_test_orders(yaml_path: str) -> List[SimpleNamespace]:
    """
    Load test orders from YAML files.
    Returns objects that mimic Shopify order structure.
    """
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Convert dictionary to object recursively
    def dict_to_obj(d):
        if isinstance(d, dict):
            return SimpleNamespace(**{k: dict_to_obj(v) for k, v in d.items()})
        elif isinstance(d, list):
            return [dict_to_obj(x) for x in d]
        return d

    return dict_to_obj(data)