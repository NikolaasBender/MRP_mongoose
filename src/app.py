from flask import Flask, render_template
from bags import Bag
import pandas as pd
from db_connector import MRPDatabase

from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

database_connection = MRPDatabase('inventory.db')

@app.route('/')
def index():
    # Load all of the files to cut and quantities
    cut_table = database_connection.get_cut_list()
    # print(cut_table)
    
    # convert the sql result to a pandas DataFrame
    panel_data = []
    for row in cut_table:
        # Access by key instead of unpacking
        part_name = row['part_name']
        file_path = row['file_path']
        color_id = row['color']
        quantity = row['quantity']
        cut_id = row.get('cut_id') # Ensure we get cut_id
        status = row.get('status', 'pending') # Default to pending
        
        # look up the color name from the colors table
        color_name = database_connection.get_color_name(color_id)
        
        # Only show pending items in main list (optional: could filter in template)
        if status != 'done':
            panel_data.append({
                'cut_id': cut_id,
                'part_name': part_name,
                'file_path': file_path,
                'color': color_name,
                'quantity': quantity,
                'status': status
            })
    
    # Convert to pandas DataFrame for easy manipulation
    if panel_data:
        df = pd.DataFrame(panel_data)
        panels = df.to_dict('records')
    else:
        panels = []
    
    return render_template('index.html', panels=panels)

@app.route('/mark_done/<int:cut_id>', methods=['POST'])
def mark_done(cut_id):
    database_connection.mark_cut_done(cut_id)
    return redirect(url_for('index'))

@app.route('/delete/<int:cut_id>', methods=['POST'])
def delete_item(cut_id):
    database_connection.delete_cut(cut_id)
    return redirect(url_for('index'))

@app.route('/view_done')
def view_done():
    cut_table = database_connection.get_cut_list()
    panel_data = []
    for row in cut_table:
        status = row.get('status', 'pending')
        if status == 'done':
            color_name = database_connection.get_color_name(row['color'])
            panel_data.append({
                'cut_id': row.get('cut_id'),
                'part_name': row['part_name'],
                'file_path': row['file_path'],
                'color': color_name,
                'quantity': row['quantity'],
                'status': status
            })
            
    return render_template('index.html', panels=panel_data, view_mode='done')

@app.route('/undo/<int:cut_id>', methods=['POST'])
def undo_done(cut_id):
    database_connection.undo_cut_done(cut_id)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)