import shopify_connector
import os
import pprint
from datetime import datetime
from dotenv import load_dotenv
from pyactiveresource.connection import UnauthorizedAccess
from db_connector import *
from order_management import *
from bags import Bag
from shopify_connector import get_shopify_orders, pretty_print_orders

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


if __name__ == "__main__":
    # connect to shopify and get orders
    orders = get_shopify_orders(SHOP_URL, API_VERSION, ACCESS_TOKEN, API_KEY)
    if orders:
        pretty_print_orders(orders)
        for order in orders:
            try:
                order_manager.add_order(order)
            except Exception as e:
                print(f"Error processing order {order.name}: {e}")
            print()

    print("-" * 40)

