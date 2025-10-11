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
import multiprocessing 
import time

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
QUERY_INTERVAL = float(os.getenv("QUERY_INTERVAL", "3"))  # Default to 3 seconds if not set

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
# Get the absolute path to the directory containing main.py (which is 'src')
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the 'templates' folder, which is one level up
# e.g., /workspaces/bullmose/src/.. /templates/  ==> /workspaces/bullmose/templates/
template_dir = os.path.join(base_dir, '..', 'templates')

# Initialize the Flask app outside the function
app = Flask(__name__, template_folder=template_dir)

# NOTE: The database connection and logic remain the same, 
# relying on the globally defined 'database' object (or the file 'inventory.db').
@app.route('/')
def index():
    """
    Renders the index page showing the current aggregated cut list 
    by reading from the shared database file.
    """
    colors = database.get_unique_colors()
    # Use the globally initialized database connection
    df = database.get_full_cut_list_dataframe()
    
    return render_template('index.html', panels=df.to_dict('records'), colors=colors)

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

def run_order_processing():
    """
    Function to handle order processing logic, designed to be run in the main process.
    """
    while True:
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

        time.sleep(QUERY_INTERVAL)  # Wait before fetching orders again

# =========================================================================
# MAIN EXECUTION
# =========================================================================

if __name__ == "__main__":
    args = parse_args()

    # 1. START THE WEB SERVER PROCESS
    server_process = multiprocessing.Process(target=run_flask_server)
    server_process.start()

    # 2. RUN THE ORDER PROCESSING IN THE MAIN PROCESS
    order_process = multiprocessing.Process(target=run_order_processing)
    order_process.start()
    order_process.join()  # Wait for the order processing to finish
    
    
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
    order_process.terminate()
    server_process.join()
    print("Server stopped. Program exit.")