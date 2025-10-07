import pytest
from bags import Bag, Panel, Zipper, Buckle, Webbing
import tempfile
import os

@pytest.fixture
def sample_yaml_file():
    """Fixture to create a temporary YAML file for testing"""
    test_yaml = """
bag:
  name: "Test Bag"
  fabric_panels:
    - {name: "Front Panel", shop_map: "Main Color", file_path: "front.dng"}
    - {name: "Bottom Panel", shop_map: "Accent 1", file_path: "bottom.dng"}
  zippers:
    - {pitch: 5, length: 30, color: "Black", name: "Main Zipper"}
  buckles:
    - {size: 3, color: "Silver", name: "Side Buckle"}
  webbings:
    - {width: 20, length: 100, color: "Black", name: "Shoulder Strap"}
"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.yaml')
    temp_file.write(test_yaml)
    temp_file.close()
    
    yield temp_file.name  # Provide the filename to the test
    
    os.unlink(temp_file.name)  # Cleanup after test

@pytest.fixture
def sample_bag():
    """Fixture to create a sample bag instance"""
    panels = [
        Panel(name="Front Panel", shop_map="Main Color", file_path="front.dng"),
        Panel(name="Back Panel", shop_map="Accent 1", file_path="back.dng")
    ]
    zippers = [
        Zipper(pitch=5, length=30, color="Black", name="Main Zipper")
    ]
    buckles = [
        Buckle(size=3, color="Silver", name="Side Buckle")
    ]
    webbings = [
        Webbing(width=20, length=100, color="Black", name="Shoulder Strap")
    ]
    return Bag("Test Bag", panels, zippers, buckles, webbings)

def test_bag_initialization(sample_bag):
    """Test if Bag object is initialized correctly"""
    assert sample_bag.name == "Test Bag"
    assert len(sample_bag.panels) == 2
    assert len(sample_bag.zippers) == 1
    assert len(sample_bag.buckles) == 1
    assert len(sample_bag.webbings) == 1

def test_get_panel_files(sample_bag):
    """Test if get_panel_files returns correct file paths"""
    expected_files = ["front.dng", "back.dng"]
    assert sample_bag.get_panel_files() == expected_files

def test_from_yaml(sample_yaml_file):
    """Test if bags can be created from YAML file"""
    bags = Bag.from_yaml(sample_yaml_file)
    assert len(bags) == 1
    
    bag = bags[0]
    assert bag.name == "Test Bag"
    assert len(bag.panels) == 2
    assert bag.panels[0].file_path == "front.dng"
    assert bag.zippers[0].color == "Black"
    assert bag.buckles[0].size == 3
    assert bag.webbings[0].width == 20

def test_invalid_yaml_path():
    """Test if attempting to load from non-existent file raises error"""
    with pytest.raises(FileNotFoundError):
        Bag.from_yaml("nonexistent.yaml")