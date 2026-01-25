Phase 2.1: Configuration & Models

    [x] Task 1: Update src/bags_configs.yaml structure.

        [x] Add color_order_map list to standard bags.

        [x] Add inventory_policy dict (min_stock, batch_size) to standard bags.

    [x] Task 2: Update src/db_connector.py.

        [x] Restore detailed cut_list table (instead of dropping).

        [x] Create jobs table logic.

        [x] Create finished_goods table logic.

Phase 2.2: Parsing & Logic

    [x] Task 3: Implement Parsing Logic in src/bags.py.

        [x] Create function explode_standard_colors(color_string, map_config).
        
        [x] Implement fuzzy matching for bag names.
        
        [x] Implement detailed cut list generation (Panel/Hardware decomposition).

    [x] Task 4: Implement Triage Logic in src/order_management.py.

        [x] Add check_inventory(sku) function.

        [x] Add create_replenishment_job(sku, config) function.

        [x] Refactor main loop to use the new Decision Tree.

Phase 2.3: Interface

    [x] Task 5: Update Flask Routes in src/main.py.

        [x] Add routes for /cutting, /sewing, and /inventory.

        [x] Add API endpoints for state transitions (/api/mark_cut, /api/mark_sewn).

    [x] Task 6: Update Frontend Templates.

        [x] Create cutting.html (Detailed Cut List table).

        [x] Create sewing.html (Job queue).

        [x] Create inventory.html (Stock adjustment).

Phase 2.4: Testing

    [x] Task 7: Mock Data & Integration Test.

        [x] Inject a mock Shopify order with "Navy/Green/Yellow".

        [x] Verify it correctly parses into 3 distinct panels.

        [x] Verify it triggers a Replenishment Job if stock is 0.
        
        [x] Verified fuzzy string matching for Product Titles.

Phase 2.5: Efficiency Tools

    [x] Task 8: Implement Color Filtering in Cutting Interface.

        [x] Add filtering logic to db_connector (get_pending_cut_colors).

        [x] Update cutting.html with color filter dropdown.

        [x] Update /cutting route to handle color param.