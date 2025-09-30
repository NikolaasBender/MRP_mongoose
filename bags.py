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

class Bag:
    def __init__(self, name: str, panels: List[Panel], zippers: List[Zipper], 
                 buckles: List[Buckle], webbings: List[Webbing]):
        self.name = name
        self.panels = panels
        self.zippers = zippers
        self.buckles = buckles
        self.webbings = webbings

    def get_panel_files(self) -> List[str]:
        return [panel.file_path for panel in self.panels]
    
    def get_panel_by_shop_map(self, shop_map: str) -> Panel:
        for panel in self.panels:
            if panel.shop_map == shop_map:
                return panel
        raise ValueError(f"No panel found for shop map: {shop_map}")

    @classmethod
    def from_yaml(cls, yaml_path: str) -> List['Bag']:
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load_all(f)  # Use load_all for multiple documents
            bags = []
            
            for bag_data in data:
                panels = [Panel(**panel) for panel in bag_data['bag']['fabric_panels']]
                zippers = [Zipper(**zipper) for zipper in bag_data['bag']['zippers']]
                buckles = [Buckle(**buckle) for buckle in bag_data['bag']['buckles']]
                webbings = [Webbing(**webbing) for webbing in bag_data['bag']['webbings']]
                
                bags.append(cls(
                    name=bag_data['bag']['name'],
                    panels=panels,
                    zippers=zippers,
                    buckles=buckles,
                    webbings=webbings
                ))
            
            return bags