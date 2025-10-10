import shopify_connector
from db_connector import *
import shopify
from bags import Bag
import difflib


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

    
    def fuzzy_match_panel_name(self, name: str, properties: dict) -> str | None:
        """
        Finds the closest fuzzy match for 'name' within a list provided in 'properties'.

        The list to search must be under the key 'panel_list' in the properties dict.

        Args:
            name: The string to match (e.g., "Accent 1").
            properties: A dictionary that *must* contain a key 'panel_list'
                        with the list of potential matches (e.g., ["Main Panel", ...]).

        Returns:
            The closest matching string from the list, or None if the list is missing
            or empty.
        """
        # 1. Get the list of choices from the properties dictionary
        choices = properties.keys()

        if not choices:
            print("Error: 'panel_list' not found or is empty in properties dictionary.")
            return None

        # 2. Use difflib.get_close_matches to find the best match
        #    - n=1: We only want the single best match
        #    - cutoff=0.6: Only return a match if the similarity ratio is at least 0.6
        #                  (You can adjust this cutoff as needed)
        best_match = difflib.get_close_matches(
            word=name,
            possibilities=choices,
            n=1,
            cutoff=0.4
        )

        # 3. Return the result
        if best_match:
            # get_close_matches returns a list, so we return the first/only element
            return best_match[0]
        else:
            # No match found above the cutoff threshold
            return None


    def add_order(self, order: dict):
        for item in order['line_items']:
            if item['properties']:
                # make properties a dictionary
                props = item['properties']
                # get color set property
                if props['Color Set'] == "Custom":
                    print("Custom order detected")
                    # get item type
                    title = item['title']
                    # get bag data by name
                    bag_data = self.get_bag_data_by_name(title)
                    # match panels and colors to the properties
                    for panel in bag_data.fabric_panels:
                        requested_panel_color = props[self.fuzzy_match_panel_name(panel.shop_map, props)]
                        # add this panel to the cut list
                        self.database.add_to_cut_list(panel.name, panel.file_path, requested_panel_color, 1)
                else: 
                # ready to ship
                    # put item through the system
                    # self.the_system(item['title'], props["Color Set"], item['quantity'])
                    print("Ready to ship order detected")

            else:
                raise Exception("Item does not have properties")
        
