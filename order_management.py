import shopify
from db_connector import *


class OrderManager:
    def __init__(self, db_interface):
        self.database = db_interface

    def the_system(self, name: str, color: str, quantity: int):
        # check if there is stock of this item in this color
        available_items = self.database.get_inventory_count(name, color)
        if available_items <  self.database.get_min_items(name, color):
            


    def add_order(self, order: shopify.resources.order.Order):
        for item in order.line_items:
            if hasattr(item, 'properties') and item.properties:
                print("      Properties:")
                prop  = item.properties[0]
                if prop.name == "Color Set":
                    if prop.value == "Custom":
                    # get item type
                        item.title
                    else: 
                    # ready to ship
                        # put item through the system
