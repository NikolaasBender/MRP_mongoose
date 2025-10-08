from flask import Flask, render_template
from bags import Bag
import pandas as pd
from db_connector import MRPDatabase

app = Flask(__name__)

database_connection = MRPDatabase('inventory.db')

@app.route('/')
def index():
    # Load all of the files to cut and quantities
    cut_table = database_connection.get_cut_list()
    print(cut_table)
    
    # convert the sql result to a pandas DataFrame
    panel_data = []
    for row in cut_table:
        part_name, file_path, color_id, quantity = row
        # look up the color name from the colors table
        color_name = database_connection.get_color_name(color_id)
        panel_data.append({
            'part_name': part_name,
            'file_path': file_path,
            'color': color_name,
            'quantity': quantity
        })
    
    # Convert to pandas DataFrame for easy manipulation
    df = pd.DataFrame(panel_data)
    
    return render_template('index.html', panels=df.to_dict('records'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)