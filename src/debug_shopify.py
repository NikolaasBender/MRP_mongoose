import os
import pprint
from dotenv import load_dotenv
from shopify_connector import get_shopify_orders

# Load environment variables
load_dotenv()

SHOP_URL = os.getenv("SHOPIFY_SHOP_URL")
API_VERSION = os.getenv("SHOPIFY_API_VERSION")
API_KEY = os.getenv("SHOPIFY_API_KEY")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

def main():
    print("Fetching orders from Shopify...")
    orders = get_shopify_orders(SHOP_URL, API_VERSION, ACCESS_TOKEN, API_KEY)
    
    if orders:
        print(f"\nSuccessfully fetched {len(orders)} orders.\n")
        for i, order in enumerate(orders):
            print(f"--- Order {i+1} ---")
            pprint.pprint(order)
            print("-" * 50)
    else:
        print("No orders fetched.")

if __name__ == "__main__":
    main()
