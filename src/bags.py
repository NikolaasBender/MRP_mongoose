from dataclasses import dataclass
from typing import List
import yaml
from logger import setup_logger

logger = setup_logger()

@dataclass
class Panel:
    name: str
    shop_map: str
    file_path: str
    material_set: str = None

@dataclass
class Hardware:
    size: int
    color: str
    name: str

@dataclass
class RollGood:
    name: str
    shop_map: str
    len: int
    material_set: str
    quantity: int = 1
    material_id: str = None
    web_attribute_id: str = None

@dataclass
class cutLineItem:
    panel_name: str
    file_path: str
    color: str

@dataclass
class Bag:
    name: str
    fabric_panels: List[Panel]
    hardware: List[Hardware]
    roll_goods: List[RollGood]
    color_order_map: List[str] = None
    inventory_policy: dict = None

    def get_panel_files(self) -> List[str]:
        return [panel.file_path for panel in self.fabric_panels]
    
    def get_panel_by_shop_map(self, shop_map: str) -> Panel:
        for panel in self.panels:
            if panel.shop_map == shop_map:
                return panel
        raise ValueError(f"No panel found for shop map: {shop_map}")

    @staticmethod
    def _filter_args(cls, data):
        """Helper to filter dictionary keys to match dataclass fields"""
        # Get field names from the dataclass
        field_names = {f for f in cls.__annotations__}
        return {k: v for k, v in data.items() if k in field_names}

    @classmethod
    def from_yaml(cls, yaml_path: str) -> List['Bag']:
        """Load bags from YAML configuration file"""
        bags = []
        
        with open(yaml_path, 'r') as f:            
            try:
                # Load all documents
                documents = list(yaml.safe_load_all(f))
                
                for doc in documents:
                    if doc and isinstance(doc, dict) and 'bag' in doc:
                        bag_data = doc['bag']
                        try:
                            # Convert components with more robust error handling
                            panels = [Panel(**cls._filter_args(Panel, p)) for p in bag_data.get('fabric_panels', [])]
                            hardware = [Hardware(**cls._filter_args(Hardware, h)) for h in bag_data.get('hardware', [])]
                            rolls = [RollGood(**cls._filter_args(RollGood, w)) for w in bag_data.get('roll_goods', [])]
                            
                            new_bag = cls(
                                name=bag_data['name'],
                                fabric_panels=panels,
                                hardware=hardware,
                                roll_goods=rolls,
                                color_order_map=bag_data.get('color_order_map', []),
                                inventory_policy=bag_data.get('inventory_policy', {})
                            )
                            bags.append(new_bag)
                        except Exception as e:
                            logger.error(f"Error creating bag object: {str(e)}")
                    else:
                        logger.warning("Document is not a valid bag configuration")
                
                logger.info(f"Total bags loaded: {len(bags)}")
                return bags
                
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML: {str(e)}")
                raise
    
    def explode_standard_colors(self, color_string: str) -> dict:
        """
        Parses a Slash-delimited color string into a dictionary mapping shop_map keys to colors.
        Uses self.color_order_map to determine the mapping.
        """
        if not self.color_order_map:
            return {}

        colors = [c.strip() for c in color_string.split('/')]
        mapped_colors = {}
        
        for i, key in enumerate(self.color_order_map):
            if i < len(colors):
                mapped_colors[key] = colors[i]
            else:
                # If we run out of colors, maybe use the last one? 
                # Or leave it empty? Design doc implies exact mapping.
                # Assuming fallback to last regular color or 'Default' if completely missing is risky.
                # For now, let's just map what we have.
                pass
        
        return mapped_colors

    def generate_cut_list(self, order: dict) -> List[cutLineItem]:
        """
        Generate a cut list based on the bag configuration and order details.
        
        Args:
            order: A dictionary representing the Shopify order. 
                     Expected to have 'line_items' with 'properties'.
        Returns:
            List of cutLineItem representing the cut list.
        """

        cut_list = []
        
        for item in order.get('line_items', []):
            if item['title'] != self.name:
                continue  # Skip items that don't match this bag
            
            # Ensure properties is a dict
            properties_raw = item.get('properties', {})
            if isinstance(properties_raw, list):
                properties = {prop['name']: prop['value'] for prop in properties_raw}
            else:
                properties = properties_raw            
            quantity = item.get('quantity', 1)
            
            # Process fabric panels
            for panel in self.fabric_panels:
                color = properties.get(panel.shop_map, 'Default Color')
                cut_list.append(cutLineItem(
                    panel_name=panel.name,
                    file_path=panel.file_path,
                    color=color
                ))
            
            # Process webbings / roll goods
            for webbing in self.roll_goods:
                # Try to get color from properties using shop_map, fallback to material_set
                color = properties.get(webbing.shop_map, webbing.material_set)
                
                total_qty = quantity * webbing.quantity
                
                for _ in range(total_qty):
                    cut_list.append(cutLineItem(
                        panel_name=webbing.name,
                        file_path='-',  # No file path for webbing
                        color=color
                    ))
            

            
            # Process hardware
            for hw in self.hardware:
                color = properties.get('Hardware Color', hw.color)
                for _ in range(quantity):
                    cut_list.append(cutLineItem(
                        panel_name=hw.name,
                        file_path='-',  # No file path for hardware
                        color=color
                    ))
        
        return cut_list