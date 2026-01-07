import pytest
import sqlite3
import os
import sys
import yaml

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_connector import MRPDatabase

TEST_DB = 'test_orders_view.db'

@pytest.fixture
def db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    database = MRPDatabase(TEST_DB)
    
    yield database
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_get_all_orders(db):
    """Test retrieving and parsing orders"""
    # Create sample order data
    order1 = {
        'id': 101,
        'name': '#1001',
        'customer': {'first_name': 'John', 'last_name': 'Doe'},
        'line_items': [{'title': 'Bag'}]
    }
    order2 = {
        'id': 102,
        'name': '#1002',
        'customer': {'first_name': 'Jane', 'last_name': 'Doe'},
        'line_items': [{'title': 'Strap'}]
    }
    
    # Insert orders manually using add_order
    db.add_order(101, order1)
    db.add_order(102, order2)
    
    # Retrieve orders
    orders = db.get_all_orders()
    
    assert len(orders) == 2
    # Check order of results (DESC by ID)
    assert orders[0]['id'] == 102
    assert orders[1]['id'] == 101
    
    # Check content
    assert orders[0]['name'] == '#1002'
    assert orders[0]['customer']['first_name'] == 'Jane'

def test_invalid_yaml_handling(db):
    """Test handling of invalid YAML in orders table"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        # Insert raw invalid YAML
        cursor.execute("INSERT INTO orders (order_id, order_data) VALUES (?, ?)", (999, "invalid: : yaml"))
        conn.commit()
    
    orders = db.get_all_orders()
    assert len(orders) == 1
    assert orders[0]['id'] == 999
    assert orders[0]['name'] == 'Error Loading Data'
