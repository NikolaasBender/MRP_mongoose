import shopify_connector
import os
import pprint
from datetime import datetime
from dotenv import load_dotenv
from pyactiveresource.connection import UnauthorizedAccess
from db_connector import *
from order_management import *
from bags import Bag
from shopify_connector import get_shopify_orders, pretty_print_orders, save_orders_as_yaml
import argparse

# Load environment variables from .env file
load_dotenv()

# --- IMPORTANT SETUP ---
SHOP_URL = os.getenv("SHOPIFY_SHOP_URL")
API_VERSION = os.getenv("SHOPIFY_API_VERSION")
API_KEY = os.getenv("SHOPIFY_API_KEY")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

bags = Bag.from_yaml('bags_configs.yaml')
database = MRPDatabase('inventory.db')
order_manager = OrderManager(database, bags)

def parse_args():
    parser = argparse.ArgumentParser(description='Shopify Order Management System')
    parser.add_argument('--save-orders', action='store_true',
                       help='Save fetched orders to YAML files for testing')
    parser.add_argument('--output-dir', default='test_data',
                       help='Directory to save order YAML files (default: test_data)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # connect to shopify and get orders
    orders = get_shopify_orders(SHOP_URL, API_VERSION, ACCESS_TOKEN, API_KEY)
    if orders:
        pretty_print_orders(orders)
        
        if args.save_orders:
            save_orders_as_yaml(orders, args.output_dir)
            print(f"Saved {len(orders)} orders to {args.output_dir}/")
        else:
            for order in orders:
                try:
                    order_manager.add_order(order)
                except Exception as e:
                    print(f"Error processing order {order.name}: {e}")
                print()

    print("-" * 40)

