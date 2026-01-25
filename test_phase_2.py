import sys
import os

# Add src to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db_connector import MRPDatabase
from order_management import OrderManager
from bags import Bag
import pandas as pd
import time

def test_workflow():
    print("Setting up test environment...")
    db_file = 'test_inventory.db'
    if os.path.exists(db_file):
        os.remove(db_file)
    
    database = MRPDatabase(db_file)
    bags = Bag.from_yaml('src/bags_configs.yaml')
    order_manager = OrderManager(database, bags)

    # 1. Inject Mock Order
    print("\n1. Injecting Mock Order...")
    mock_order = {
        'id': 12345,
        'name': '#12345',
        'line_items': [
            {
                'title': 'Sling Thing', # 3 panels
                'quantity': 1,
                'properties': [
                    {'name': 'Color Set', 'value': 'Navy/Green/Yellow'}
                ]
            }
        ]
    }
    
    # Check initial inventory (should be empty)
    sku = "Sling Thing - Navy/Green/Yellow"
    assert database.get_finished_goods_count(sku) == 0
    
    order_manager.add_order(mock_order)
    
    # Verify Job Creation
    print("\n2. Verifying Job Creation...")
    jobs = database.get_jobs(status='pending')
    print(f"Pending jobs: {len(jobs)}")
    
    # Inventory policy defaults (min 5, batch 1).
    assert len(jobs) == 1
    job = jobs[0]
    assert job['sku'] == sku
    print(f"Job created: ID={job['job_id']}, SKU={job['sku']}")
    
    # 3. Verify Parsing (Task 22: Verify it parses into 3 distinct panels)
    print("\n3. Verifying Parsing Logic (Unit Test)...")
    bag_data = order_manager.get_bag_data_by_name("Sling Thing")
    mapped_colors = bag_data.explode_standard_colors("Navy/Green/Yellow")
    print(f"Mapped colors: {mapped_colors}")
    
    # color_order_map for Sling Thing is ["Left", "Right", "Top"]
    assert mapped_colors['Left'] == 'Navy'
    assert mapped_colors['Right'] == 'Green'
    assert mapped_colors['Top'] == 'Yellow'
    assert len(mapped_colors) == 3
    
    # 4. Verify Job Lifecycle (Cut -> Sew -> Done -> Inventory)
    print("\n4. Verifying Job Lifecycle...")
    
    # Mark Cut
    print("Marking Cut...")
    database.update_job_status(job['job_id'], 'cut')
    job = database.get_job(job['job_id'])
    assert job['status'] == 'cut'
    
    # Mark Sewn (Complete)
    print("Marking Sewn (Complete)...")
    database.update_job_status(job['job_id'], 'complete')
    # Add to inventory (logic copied from main.py route)
    database.add_finished_goods(job['sku'], 1, location="Production")
    
    job = database.get_job(job['job_id'])
    assert job['status'] == 'complete'
    
    # Verify Inventory
    print("Verifying Inventory...")
    stock = database.get_finished_goods_count(sku)
    print(f"Stock for {sku}: {stock}")
    assert stock == 1
    
    print("\nSuccess! Workflow verified.")
    
    # Clean up
    if os.path.exists(db_file):
        os.remove(db_file)

if __name__ == "__main__":
    test_workflow()
