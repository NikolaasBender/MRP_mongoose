from dataclasses import dataclass
from typing import List
import yaml

@dataclass
class Panel:
    name: str
    shop_map: str
    file_path: str

@dataclass
class Zipper:
    pitch: int
    length: int
    color: str
    name: str

@dataclass
class Buckle:
    size: int
    color: str
    name: str

@dataclass
class Webbing:
    width: int
    length: int
    color: str
    name: str

@dataclass
class cutLineItem:
    panel_name: str
    file_path: str
    color: str

@dataclass
class Bag:
    name: str
    fabric_panels: List[Panel]
    zippers: List[Zipper]
    buckles: List[Buckle]
    webbings: List[Webbing]

    def get_panel_files(self) -> List[str]:
        return [panel.file_path for panel in self.fabric_panels]
    
    def get_panel_by_shop_map(self, shop_map: str) -> Panel:
        for panel in self.panels:
            if panel.shop_map == shop_map:
                return panel
        raise ValueError(f"No panel found for shop map: {shop_map}")

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
                            panels = [Panel(**p) for p in bag_data.get('fabric_panels', [])]
                            zippers = [Zipper(**z) for z in bag_data.get('zippers', [])]
                            buckles = [Buckle(**b) for b in bag_data.get('buckles', [])]
                            webbings = [Webbing(**w) for w in bag_data.get('webbings', [])]
                            
                            new_bag = cls(
                                name=bag_data['name'],
                                fabric_panels=panels,
                                zippers=zippers,
                                buckles=buckles,
                                webbings=webbings
                            )
                            bags.append(new_bag)
                        except Exception as e:
                            print(f"Error creating bag object: {str(e)}")
                    else:
                        print("Document is not a valid bag configuration")
                
                print(f"\nTotal bags loaded: {len(bags)}")
                return bags
                
            except yaml.YAMLError as e:
                print(f"Error parsing YAML: {str(e)}")
                raise
        
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
            
            properties = {prop['name']: prop['value'] for prop in item.get('properties', [])}
            quantity = item.get('quantity', 1)
            
            # Process fabric panels
            for panel in self.fabric_panels:
                color = properties.get(panel.shop_map, 'Default Color')
                cut_list.append(cutLineItem(
                    panel_name=panel.name,
                    file_path=panel.file_path,
                    color=color
                ))
            
            # Process webbings
            for webbing in self.webbings:
                color = properties.get('Strap Color', webbing.color)
                for _ in range(quantity):
                    cut_list.append(cutLineItem(
                        panel_name=webbing.name,
                        file_path='-',  # No file path for webbing
                        color=color
                    ))
            
            # Process zippers
            for zipper in self.zippers:
                color = properties.get('Zipper Color', zipper.color)
                for _ in range(quantity):
                    cut_list.append(cutLineItem(
                        panel_name=zipper.name,
                        file_path='-',  # No file path for zippers
                        color=color
                    ))
            
            # Process buckles
            for buckle in self.buckles:
                color = properties.get('Buckle Color', buckle.color)
                for _ in range(quantity):
                    cut_list.append(cutLineItem(
                        panel_name=buckle.name,
                        file_path='-',  # No file path for buckles
                        color=color
                    ))
        
        return cut_list