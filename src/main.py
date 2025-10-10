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
import multiprocessing # <-- New Import for concurrency

# --- WEB SERVER IMPORTS ---
from flask import Flask, render_template
import pandas as pd
# --------------------------

# Load environment variables from .env file
load_dotenv()

# --- IMPORTANT SETUP ---
SHOP_URL = os.getenv("SHOPIFY_SHOP_URL")
API_VERSION = os.getenv("SHOPIFY_API_VERSION")
API_KEY = os.getenv("SHOPIFY_API_KEY")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

# Initialize global/shared resources
# NOTE: In a multiprocessing environment, this global state is copied.
# Since the Flask app only *reads* from the database (which is a shared file),
# and the main process *writes* to it, this setup is generally fine.
bags = Bag.from_yaml('src/bags_configs.yaml')
database = MRPDatabase('inventory.db')
order_manager = OrderManager(database, bags)

def parse_args():
    parser = argparse.ArgumentParser(description='Shopify Order Management System')
    parser.add_argument('--save-orders', action='store_true',
                       help='Save fetched orders to YAML files for testing')
    parser.add_argument('--output-dir', default='test_data',
                       help='Directory to save order YAML files (default: test_data)')
    return parser.parse_args()

# =========================================================================
# WEB SERVER LOGIC (Needs to be a standard function for multiprocessing)
# =========================================================================

# Initialize the Flask app outside the function
app = Flask(__name__)

# NOTE: The database connection and logic remain the same, 
# relying on the globally defined 'database' object (or the file 'inventory.db').
@app.route('/')
def index():
    """
    Renders the index page showing the current aggregated cut list 
    by reading from the shared database file.
    """
    # Use the globally initialized database connection
    cut_table = database.get_cut_list()
    
    panel_data = []
    for row in cut_table:
        part_name, file_path, color_id, quantity = row
        color_name = database.get_color_name(color_id)
        
        panel_data.append({
            'part_name': part_name,
            'file_path': file_path,
            'color': color_name,
            'quantity': quantity
        })
    
    # Convert to pandas DataFrame for easy manipulation and pass to template
    df = pd.DataFrame(panel_data)
    
    return render_template('index.html', panels=df.to_dict('records'))

def run_flask_server():
    """
    Function to start the Flask server, designed to be run in a separate process.
    """
    print("-" * 40)
    print("Starting Flask web server in a separate process...")
    print("Access the cut list at: http://127.0.0.1:5000/")
    print("-" * 40)
    # NOTE: Set use_reloader=False when running in a multi-process environment 
    # to prevent the reloader from accidentally starting new processes.
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

# =========================================================================
# MAIN EXECUTION
# =========================================================================

if __name__ == "__main__":
    args = parse_args()

    # 1. START THE WEB SERVER PROCESS
    server_process = multiprocessing.Process(target=run_flask_server)
    server_process.start()

    # 2. CONTINUE WITH ORDER PROCESSING IN THE MAIN PROCESS
    print("Fetching orders from Shopify in the main process...")
    
    # connect to shopify and get orders
    orders = get_shopify_orders(SHOP_URL, API_VERSION, ACCESS_TOKEN, API_KEY)
    
    if orders:
        print(f"Successfully fetched {len(orders)} orders.")
        
        if args.save_orders:
            save_orders_as_yaml(orders, args.output_dir)
            print(f"Saved {len(orders)} orders to {args.output_dir}/")
        else:
            for order in orders:
                try:
                    # This updates the database file, which the web server reads
                    order_manager.add_order(order)
                    print(f"Processed order {order['name']}")
                except Exception as e:
                    print(f"Error processing order {order.get('name', 'UNKNOWN')}: {e}")

        print("-" * 40)
        print("Order processing complete. The web server is still running.")
    else:
        print("No orders fetched or an error occurred during connection.")
    
    # Optional: Keep the main process alive so the web server doesn't shut down
    # when the order fetching is done. You can use a loop or simply join 
    # the server process, though joining will stop the main process from exiting.
    # A simple way to keep it alive is to wait for the user to press Enter.
    print("The server will continue to run in the background.")
    try:
        input("Press Enter to stop the server and exit the program...\n")
    except EOFError:
        # Handle case where input is piped (non-interactive session)
        print("Exiting...")
    except KeyboardInterrupt:
        print("\nStopping server...")
    
    # 3. CLEANUP: Terminate the server process when the user is done
    server_process.terminate()
    server_process.join()
    print("Server stopped. Program exit.")