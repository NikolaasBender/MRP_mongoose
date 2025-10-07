import pytest
from shopify_connector import save_orders_as_yaml, load_test_orders
import os
import yaml
from types import SimpleNamespace
from datetime import datetime

@pytest.fixture
def sample_order_data():
    """Fixture providing sample order data"""
    return {
        'id': 12345,
        'name': '#1001',
        'created_at': '2025-09-26T01:33:25-04:00',
        'line_items': [
            {
                'title': 'Basket Boss',
                'quantity': 1,
                'properties': [
                    {'name': 'Color Set', 'value': 'Ready To Ship'},
                    {'name': 'Color', 'value': 'Navy/Green/Yellow'}
                ]
            }
        ]
    }

@pytest.fixture
def test_yaml_file(sample_order_data, tmp_path):
    """Fixture creating a temporary YAML file with sample data"""
    file_path = tmp_path / "test_order.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(sample_order_data, f)
    return file_path

def test_load_test_orders(test_yaml_file):
    """Test loading orders from YAML file"""
    order = load_test_orders(test_yaml_file)
    
    # Check basic order properties
    assert order.id == 12345
    assert order.name == '#1001'
    assert order.created_at == '2025-09-26T01:33:25-04:00'
    
    # Check line items
    assert len(order.line_items) == 1
    item = order.line_items[0]
    assert item.title == 'Basket Boss'
    assert item.quantity == 1
    
    # Check properties
    assert len(item.properties) == 2
    assert item.properties[0].name == 'Color Set'
    assert item.properties[0].value == 'Ready To Ship'
    assert item.properties[1].name == 'Color'
    assert item.properties[1].value == 'Navy/Green/Yellow'

def test_load_test_orders_file_not_found():
    """Test handling of non-existent YAML file"""
    with pytest.raises(FileNotFoundError):
        load_test_orders('nonexistent.yaml')

def test_save_and_load_orders(tmp_path, sample_order_data):
    """Test full cycle of saving and loading orders"""
    # Create a SimpleNamespace object that mimics a Shopify order
    class MockOrder:
        pass
    
    order = MockOrder()
    for key, value in sample_order_data.items():
        setattr(order, key, value)
    
    # Save the order
    output_dir = tmp_path / "test_output"
    save_orders_as_yaml([order], str(output_dir))
    
    # Verify file was created
    assert len(list(output_dir.iterdir())) == 1
    
    # Load the saved file
    saved_file = next(output_dir.iterdir())
    loaded_order = load_test_orders(str(saved_file))
    
    # Verify loaded data matches original
    assert loaded_order.id == sample_order_data['id']
    assert loaded_order.name == sample_order_data['name']
    assert len(loaded_order.line_items) == len(sample_order_data['line_items'])