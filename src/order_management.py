import shopify_connector
from db_connector import *
import shopify
from bags import Bag
from logger import setup_logger
from datetime import datetime

logger = setup_logger()

class OrderManager:
    def __init__(self, db_interface, bags=None):
        self.database = db_interface
        self.bags = bags or []
        if not bags:
            logger.warning("No bags provided to OrderManager.")

    def get_bag_data_by_name(self, name: str):
        normalized_name = name.strip().lower()
        for bag in self.bags:
            if bag.name.strip().lower() == normalized_name:
                return bag
        return None

    def check_inventory(self, sku: str) -> bool:
        """Checks if there is stock of this finished good."""
        count = self.database.get_finished_goods_count(sku)
        return count > 0

    def create_replenishment_job(self, sku: str, config: dict):
        """Creates jobs to replenish stock based on policy."""
        batch_size = config.get('batch_size', 1)
        # min_stock = config.get('min_stock', 0)
        
        logger.info(f"Creating replenishment jobs for {sku}, batch size: {batch_size}")
        
        # Generate a batch ID for this group of jobs
        batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{sku.replace(' ', '_')}"
        
        for _ in range(batch_size):
            self.database.add_job(sku, batch_id)

    def add_order(self, order: dict):
        if not self.database.add_order(order['id'], order):
            logger.info(f"Order {order['id']} already processed.")
            return

        logger.info(f"Processing Order {order['id']}")
        
        for item in order.get('line_items', []):
            title = item['title']
            bag_data = self.get_bag_data_by_name(title)
            
            if not bag_data:
                logger.warning(f"Skipping item '{title}' — no matching bag in configs. Check bags_configs.yaml.")
                continue

            # properties is already a dict from shopify_connector
            properties = item.get('properties', {})
            # If it happens to be a list (old format), convert it
            if isinstance(properties, list):
                 properties = {prop['name']: prop['value'] for prop in properties}
            quantity = item.get('quantity', 1)

            # Determine "Color String" or style
            # Priority: 'Color Set' > 'Color' > 'Default'
            color_set = properties.get('Color Set')
            if not color_set:
                 color_set = properties.get('Color', 'Default')

            if color_set == "Custom":
                # Treat Custom as a unique SKU or flow? 
                # For now, simplistic approach:
                sku = f"{bag_data.name} - Custom"
            else:
                sku = f"{bag_data.name} - {color_set}"

            logger.info(f"Line Item: {title}, SKU: {sku}, Qty: {quantity}")

            for _ in range(quantity):
                if self.check_inventory(sku):
                    logger.info(f"Stock available for {sku}. Allocating from Finished Goods.")
                    # Decrement stock (add negative record)
                    self.database.add_finished_goods(sku, -1, location="Shipped") 
                else:
                    logger.info(f"Stock NOT available for {sku}. Creating Replenishment Job.")
                    self.create_replenishment_job(sku, bag_data.inventory_policy)
                    
                    # --- DETAILED CUT LIST GENERATION ---
                    logger.info(f"Generating detailed cut list for {sku}...")
                    cut_items = bag_data.generate_cut_list(order)
                    for cut_item in cut_items:
                        self.database.add_cut_item(
                            panel_name=cut_item.panel_name,
                            file_path=cut_item.file_path,
                            color=cut_item.color,
                            quantity=1 # generate_cut_list flattens quantities, so we add 1 per item returned
                        )
                    logger.info(f"Added {len(cut_items)} items to cut list.")
