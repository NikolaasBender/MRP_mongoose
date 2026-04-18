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
from logger import setup_logger

from werkzeug.utils import secure_filename
import yaml

# --- WEB SERVER IMPORTS ---
from flask import Flask, render_template, redirect, url_for, request
import pandas as pd
# --------------------------

from config_loader import load_config, save_config

# Load environment variables from .env file
load_dotenv()

# Setup Logger
logger = setup_logger()

# --- IMPORTANT SETUP ---
# Initial load
initial_config = load_config()
SHOP_URL = initial_config.get("SHOPIFY_SHOP_URL")
API_VERSION = initial_config.get("SHOPIFY_API_VERSION")
API_KEY = initial_config.get("SHOPIFY_API_KEY")
ACCESS_TOKEN = initial_config.get("SHOPIFY_ACCESS_TOKEN")
QUERY_INTERVAL = float(initial_config.get("QUERY_INTERVAL", "3"))  # Default to 3 seconds if not set
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'assets')

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
app = Flask(__name__, template_folder=template_dir, static_folder='static')

# NOTE: The database connection and logic remain the same, 
# relying on the globally defined 'database' object (or the file 'inventory.db').
@app.route('/')
def index():
    return redirect(url_for('cutting'))

@app.route('/add_bag', methods=['GET', 'POST'])
def add_bag():
    if request.method == 'GET':
        return render_template('add_bag.html')
    
    if request.method == 'POST':
        try:
            f = request.form
            
            # 1. Parse Basic Info
            bag_data = {
                'name': f.get('name'),
                'inventory_policy': {
                    'min_stock': int(f.get('min_stock', 5)),
                    'batch_size': int(f.get('batch_size', 1))
                },
                'color_order_map': f.getlist('color_order_map[]'),
                'fabric_panels': [],
                'hardware': [],
                'roll_goods': []
            }
            
            # 2. Parse Panels & Upload Files
            panel_names = f.getlist('panel_name[]')
            panel_maps = f.getlist('panel_shop_map[]')
            panel_materials = f.getlist('panel_material[]')
            panel_files = request.files.getlist('panel_file[]')
            
            # Ensure assets directory exists
            if not os.path.exists(ASSETS_DIR):
                os.makedirs(ASSETS_DIR)

            for i, name in enumerate(panel_names):
                if not name: continue # Skip empty rows
                
                filename = "placeholder.svg"
                if i < len(panel_files) and panel_files[i].filename:
                    file = panel_files[i]
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(ASSETS_DIR, filename))
                
                bag_data['fabric_panels'].append({
                    'name': name,
                    'shop_map': panel_maps[i] if i < len(panel_maps) else "",
                    'file_path': filename,
                    'material_set': panel_materials[i] if i < len(panel_materials) else "Default Fabric"
                })

            # 3. Parse Hardware
            hw_names = f.getlist('hw_name[]')
            hw_sizes = f.getlist('hw_size[]')
            hw_colors = f.getlist('hw_color[]')
            
            for i, name in enumerate(hw_names):
                if not name: continue
                bag_data['hardware'].append({
                    'name': name,
                    'size': int(hw_sizes[i]) if i < len(hw_sizes) and hw_sizes[i] else 0,
                    'color': hw_colors[i] if i < len(hw_colors) else "Silver"
                })

            # 4. Parse Roll Goods
            rg_names = f.getlist('webbing_name[]')
            rg_maps = f.getlist('webbing_shop_map[]')
            rg_lens = f.getlist('webbing_len[]')
            rg_mats = f.getlist('webbing_material[]')
            rg_qtys = f.getlist('webbing_qty[]')
            
            for i, name in enumerate(rg_names):
                if not name: continue
                bag_data['roll_goods'].append({
                    'name': name,
                    'shop_map': rg_maps[i] if i < len(rg_maps) else "",
                    'len': int(rg_lens[i]) if i < len(rg_lens) and rg_lens[i] else 0,
                    'material_set': rg_mats[i] if i < len(rg_mats) else "Default",
                    'quantity': int(rg_qtys[i]) if i < len(rg_qtys) and rg_qtys[i] else 1
                })

            # 5. Append to YAML
            # We wrap it in a 'bag' key as per existing schema
            full_doc = {'bag': bag_data}
            
            with open('src/bags_configs.yaml', 'a') as f:
                f.write('\n---\n')
                yaml.dump(full_doc, f, sort_keys=False)
                
            logger.info(f"Successfully added new bag: {bag_data['name']}")
            
            # Reload bags in memory (for this process only)
            global bags
            bags = Bag.from_yaml('src/bags_configs.yaml')
            # Update order_manager's reference
            order_manager.bags = bags
            
            return redirect(url_for('cutting'))

        except Exception as e:
            logger.error(f"Error adding bag: {e}")
            return f"Error adding bag: {str(e)}", 500

@app.route('/cutting')
def cutting():
    # Get filter from query params
    selected_color = request.args.get('color', 'ALL')
    
    # Fetch detailed cut list items (filtered)
    cut_items = database.get_cut_list(color=selected_color)
    
    # Fetch available colors for the dropdown
    available_colors = database.get_pending_cut_colors()
    
    return render_template('cutting.html', cut_items=cut_items, available_colors=available_colors, selected_color=selected_color)

@app.route('/sewing')
def sewing():
    jobs = database.get_jobs(status='cut')
    return render_template('sewing.html', jobs=jobs)

@app.route('/inventory')
def inventory():
    finished_goods = database.get_all_finished_goods()
    return render_template('inventory.html', goods=finished_goods)

@app.route('/api/mark_cut/<int:job_id>', methods=['POST'])
def mark_cut(job_id):
    database.update_job_status(job_id, 'cut')
    return redirect(url_for('cutting'))

@app.route('/api/mark_sewn/<int:job_id>', methods=['POST'])
def mark_sewn(job_id):
    job = database.get_job(job_id)
    if job:
        database.update_job_status(job_id, 'complete')
        # Add to inventory upon completion
        database.add_finished_goods(job['sku'], 1, location="Production")
    return redirect(url_for('sewing'))

@app.route('/api/mark_cut_item/<int:item_id>', methods=['POST'])
def mark_cut_item(item_id):
    database.update_cut_item_status(item_id, 'done')
    color = request.form.get('color', 'ALL')
    return redirect(url_for('cutting', color=color))

@app.route('/logs')
def view_logs():
    """
    Renders the logs page.
    """
    module = request.args.get('module', 'ALL')
    level = request.args.get('level', 'ALL')
    
    # Defaults
    db_module = module if module != 'ALL' else None
    db_level = level if level != 'ALL' else None
    
    logs = database.get_logs(limit=200, level=db_level, module=db_module)
    
    return render_template('logs.html', logs=logs, current_module=module, current_level=level)

@app.route('/orders')
def view_orders():
    """
    Renders the orders page.
    """
    orders = database.get_all_orders(limit=50) # Limit to 50 for now
    return render_template('orders.html', orders=orders)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Save config
        new_config = {
            "SHOPIFY_SHOP_URL": request.form.get("shop_url"),
            "SHOPIFY_API_VERSION": request.form.get("api_version"),
            "SHOPIFY_API_KEY": request.form.get("api_key"),
            "SHOPIFY_ACCESS_TOKEN": request.form.get("access_token"),
            "QUERY_INTERVAL": request.form.get("query_interval", "3")
        }
        if save_config(new_config):
            logger.info("Configuration updated successfully.")
        else:
            logger.error("Failed to update configuration.")
        return redirect(url_for('settings'))
    
    # Load current config for display
    config = load_config()
    return render_template('settings.html', config=config)

@app.route('/help')
def help_page():
    return render_template('help.html')


def run_flask_server():
    """
    Function to start the Flask server, designed to be run in a separate process.
    """
    logger.info("Starting Flask web server in a separate process...")
    # NOTE: Set use_reloader=False when running in a multi-process environment 
    # to prevent the reloader from accidentally starting new processes.
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

def run_order_processing():
    """
    Function to handle order processing logic, designed to be run in the main process.
    """
    while True:
        # 2. CONTINUE WITH ORDER PROCESSING IN THE MAIN PROCESS
        logger.info("Fetching orders from Shopify in the main process...")
        
        # Reload config to get latest values
        config = load_config()
        shop_url = config.get("SHOPIFY_SHOP_URL")
        api_version = config.get("SHOPIFY_API_VERSION")
        access_token = config.get("SHOPIFY_ACCESS_TOKEN")
        api_key = config.get("SHOPIFY_API_KEY")
        query_interval = float(config.get("QUERY_INTERVAL", "3"))

        # connect to shopify and get orders
        orders = get_shopify_orders(shop_url, api_version, access_token, api_key)
        
        if orders:
            logger.info(f"Successfully fetched {len(orders)} orders.")
            
            if args.save_orders:
                save_orders_as_yaml(orders, args.output_dir)
                logger.info(f"Saved {len(orders)} orders to {args.output_dir}/")
            else:
                for order in orders:
                    try:
                        # This updates the database file, which the web server reads
                        order_manager.add_order(order)
                        logger.info(f"Processed order {order['name']}")
                    except Exception as e:
                        logger.error(f"Error processing order {order.get('name', 'UNKNOWN')}: {e}")

            logger.info("Order processing cycle complete.")
        else:
            logger.info("No orders fetched or an error occurred during connection.")

        time.sleep(query_interval)  # Wait before fetching orders again

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
    logger.info("The server will continue to run in the background.")
    try:
        input("Press Enter to stop the server and exit the program...\n")
    except EOFError:
        # Handle case where input is piped (non-interactive session)
        logger.info("Exiting...")
    except KeyboardInterrupt:
        logger.info("Stopping server...")
    
    # 3. CLEANUP: Terminate the server process when the user is done
    server_process.terminate()
    order_process.terminate()
    server_process.join()
    logger.info("Server stopped. Program exit.")