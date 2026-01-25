import pytest
import os
import tempfile
import yaml
from datetime import datetime
from db_connector import MRPDatabase
from order_management import OrderManager
from bags import Bag, Panel, RollGood, Hardware
from logger import setup_logger

logger = setup_logger()

# --- Fixtures ---

@pytest.fixture
def temp_db():
    """Creates a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = MRPDatabase(path)
    yield db
    os.remove(path)

@pytest.fixture
def sample_bag_config():
    """Creates a sample bag configuration."""
    panels = [
        Panel(name="Front Panel", shop_map="Main Color", file_path="front.dng"),
        Panel(name="Back Panel", shop_map="Accent 1", file_path="back.dng")
    ]
    # Configure inventory policy to always batch size 1 for simplicity
    bag = Bag(name="Test Bag", hardware=[], roll_goods=[], fabric_panels=panels, inventory_policy={'batch_size': 1, 'min_stock': 0})
    return [bag]

@pytest.fixture
def order_manager(temp_db, sample_bag_config):
    """Creates an OrderManager instance with temp DB and sample bags."""
    return OrderManager(temp_db, sample_bag_config)

# --- Tests ---

def test_custom_order_creates_job(order_manager, temp_db):
    """
    Test that a 'Custom' order correctly creates a new job in the database.
    """
    # 1. Setup Mock Order
    mock_order = {
        'id': 12345,
        'name': '#1001',
        'created_at': datetime.now().isoformat(),
        'line_items': [
            {
                'title': 'Test Bag',
                'quantity': 1,
                'properties': [
                    {'name': 'Color Set', 'value': 'Custom'},
                    {'name': 'Main Color', 'value': 'Black'},
                    {'name': 'Accent 1', 'value': 'Red'}
                ]
            }
        ]
    }

    # 2. Process Order
    order_manager.add_order(mock_order)

    # 3. Verify Job Creation
    # Check jobs table
    jobs = temp_db.get_jobs()
    assert len(jobs) == 1, "Should have created exactly 1 job"
    
    job = jobs[0]
    # Based on order_management.py logic: sku = f"{title} - Custom"
    expected_sku = "Test Bag - Custom"
    assert job['sku'] == expected_sku
    assert job['status'] == 'pending'

    # Check orders table archival
    orders = temp_db.get_all_orders()
    assert len(orders) == 1
    assert orders[0]['id'] == 12345

def test_inventory_allocation_mock(order_manager, temp_db):
    """
    Test that if stock exists, it allocates from inventory instead of creating a job.
    """
    sku = "Test Bag - Default"
    
    # 1. Setup: Add stock
    temp_db.add_finished_goods(sku, 5, location="Warehouse")
    initial_stock = temp_db.get_finished_goods_count(sku)
    assert initial_stock == 5

    # 2. Process Order for that SKU
    mock_order = {
        'id': 67890,
        'name': '#1002',
        'line_items': [
            {
                'title': 'Test Bag',
                'quantity': 2,
                'properties': [
                     {'name': 'Color', 'value': 'Default'}
                ]
            }
        ]
    }
    
    order_manager.add_order(mock_order)

    # 3. Verify No New Job created
    jobs = temp_db.get_jobs()
    assert len(jobs) == 0, "Should not create job if stock is available"

    # 4. Verify Stock Decremented
    # Logic adds a negative record, so sum should be 5 - 2 = 3
    final_stock = temp_db.get_finished_goods_count(sku)
    assert final_stock == 3

def test_fuzzy_title_match(order_manager, temp_db):
    """
    Test that an order with a slightly different title (case/whitespace) still matches.
    """
    # 1. Setup Mock Order with "messed up" title
    mock_order = {
        'id': 11111,
        'name': '#FUZZY',
        'line_items': [
            {
                'title': 'test bag ', # Trailing space and lowercase
                'quantity': 1,
                'properties': [
                    {'name': 'Color Set', 'value': 'Custom'}
                ]
            }
        ]
    }

    # 2. Process Order
    order_manager.add_order(mock_order)

    # 3. Verify Job Creation
    # Should find "Test Bag" despite "test bag " input
    jobs = temp_db.get_jobs()
    assert len(jobs) == 1, "Should handle loose string matching"
    assert jobs[0]['sku'].startswith("Test Bag"), "Should map to the correct canonical bag name"

def test_real_config_flow(temp_db):
    """
    Test using the actual bags_configs.yaml file to ensure data loading works.
    """
    # 1. Load Real Config
    # Assuming test runs from root, relative path to src/bags_configs.yaml
    config_path = os.path.abspath("src/bags_configs.yaml")
    
    # Verify file exists
    assert os.path.exists(config_path), f"Config file not found at {config_path}"
    
    real_bags = Bag.from_yaml(config_path)
    assert len(real_bags) > 0, "Should load bags from real config"
    
    manager = OrderManager(temp_db, real_bags)

    # 2. Mock Order for "Basket Boss"
    # Config has: name: "Basket Boss", color_order_map: ["Main Color", "Accent 1"]
    mock_order = {
        'id': 99999,
        'name': '#REAL01',
        'created_at': datetime.now().isoformat(),
        'line_items': [
            {
                'title': 'Basket Boss',
                'quantity': 1,
                'properties': [
                    {'name': 'Main Color', 'value': 'Black'},
                    {'name': 'Accent 1', 'value': 'Red'},
                    {'name': 'Color Set', 'value': 'Custom'}
                ]
            }
        ]
    }

    # 3. Process
    manager.add_order(mock_order)

    # 4. Verify
    jobs = temp_db.get_jobs()
    assert len(jobs) == 1
    assert jobs[0]['sku'] == "Basket Boss - Custom"
