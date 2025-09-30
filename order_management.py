import shopify_connector
from db_connector import *
import shopify
from bags import Bag


class OrderManager:
    def __init__(self, db_interface, bags=None):
        self.database = db_interface
        self.bags = []
        if bags is None:
            print("No bags provided, proceeding without bag data.")
        else:
            self.bags = bags

    def the_system(self, name: str, color: str, quantity: int):
        # check if there is stock of this item in this color
        available_items = self.database.get_inventory_count(name, color)
        if available_items <  self.database.get_min_items(name, color):
            raise Exception("Not enough stock available")
        raise Exception("Not implemented yet")

    def get_bag_data_by_name(self, name: str):
        for bag in self.bags:
            if bag.name == name:
                return bag
        raise Exception(f"Bag with name {name} not found")


    def add_order(self, order: shopify.resources.order.Order):
        for item in order.line_items:
            if hasattr(item, 'properties') and item.properties:
                # make properties a dictionary
                props = {prop.name: prop.value for prop in item.properties}
                # get color set property
                if props['Color Set'] == "Custom":
                    print("Custom order detected")
                    # get item type
                    title = item.title
                    # get bag data by name
                    bag_data = self.get_bag_data_by_name(title)
                    # match panels and colors to the properties
                    for panel in bag_data.panels:
                        requested_panel_color = props[panel.shop_name]
                        # add this panel to the cut list
                        self.database.add_to_cut_list(panel.name, panel.file_path, requested_panel_color, 1)
                else: 
                # ready to ship
                    # put item through the system
                    self.the_system(item.title, props["Color Set"], item.quantity)

            else:
                raise Exception("Item does not have properties")
        
