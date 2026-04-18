
def test_real_config_flow(temp_db):
    """
    Test using the actual bags_configs.yaml file to ensure data loading works.
    """
    # 1. Load Real Config
    config_path = os.path.join(os.path.dirname(__file__), '..', 'bags_configs.yaml')
    real_bags = Bag.from_yaml(config_path)
    assert len(real_bags) > 0, "Should load bags from real config"
    
    manager = OrderManager(temp_db, real_bags)

    # 2. Mock Order for "Basket Boss"
    # Config has: name: "Basket Boss", color_order_map: ["Main Color", "Accent 1"]
    mock_order = {
        'id': 99999,
        'name': '#REAL01',
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
