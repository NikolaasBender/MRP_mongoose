import pytest
import os
import sqlite3
import tempfile
from bags import Bag, Panel, Zipper, Buckle, Webbing
import yaml

# Test reading in a yaml of bags and a custom order and producing a cut list from the information provided.
def test_generate_cut_list():
    '''
    The goal is to make a pandas dataframe that looks like this:
    |     panel name    |   file path   |  color | quantity |
    -------------------------------------------------------------
    | basket boss front | /bb/front.dng | orange | 5  |
    | basket boss back  | /bb/back.dng  | black  | 2  |
    | basket boss back  | /bb/back.dng  | blue   | 3  |
    | basket boss side  | /bb/side.dng  | black  | 4  |
    | basket boss side  | /bb/side.dng  | blue   | 1  |
    | 4inx10in webbing  |       -       |  black | 10 |
    '''
    # read in bags config
    bags = Bag.from_yaml('/workspaces/bullmose/src/bags_configs.yaml')
    print(len(bags))
    assert len(bags) == 2

    # read in orders for custom bags
    order_dict = {
        'id': 6751598051555,
        'name': '#1254',
        'created_at': '2025-10-07T18:04:34-04:00',
        'line_items': [
            {
                'title': 'B.O.F.P',
                'quantity': 1,
                'properties': [
                    {'name': 'Color Set', 'value': 'Custom'},
                    {'name': 'Main Color', 'value': 'Forest Green'},
                    {'name': 'Accent 1 (optional)', 'value': 'Cheetah'},
                    {'name': 'Accent 2 (optional)', 'value': 'Pink'},
                    {'name': 'Interior', 'value': 'Neon Yellow'},
                    {'name': 'Strap Length', 'value': '24"-48"'},
                    {'name': 'Add a note (optional)', 'value': 'I like your work.'}
                ]
            }
        ]
    }

    # send bag and order through cut list generator
    bfop = next(b for b in bags if b.name == "B.O.F.P")
    cut_list = bfop.generate_cut_list(order_dict)
    assert len(cut_list) == 8  # 4 panels + 1 zipper + 1 buckle + 1 webbing
    print(cut_list)
