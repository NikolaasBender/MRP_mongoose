import sqlite3
from sqlite3 import Error
import os
from dataclasses import dataclass
import yaml
import pandas as pd

class MRPDatabase:
    def __init__ (self, db_file_path: str, colors_file_path: str = 'src/colors.yaml'):
        self.db_name = db_file_path
        if not os.path.exists(db_file_path):
            print(f"I did not find a a database file at {db_file_path}\nCreating a new database file")
        conn = None
        self.colors_file_path = colors_file_path
        try:
            conn = sqlite3.connect(db_file_path)
            print(f"Successfully connected to the database at {db_file_path}")
            self.setup_database(db_file_path)
            conn.close()
        except:
            raise ValueError("Cant connect to database")
        
    def setup_database(self, db_file: str):
        """
        Creates a connection to the SQLite database file specified by db_file.
        If the file does not exist, it is created.

        After connecting, it calls helper functions to create the 'tasks',
        'inventory', and 'parts_to_make' tables if they don't already exist.

        Args:
            db_file (str): The name and path of the database file (e.g., 'my_project.db').
        """
        with self.get_connection() as conn:
            try:
                # Step 1: Connect to the database. This creates the file if it doesn't exist.
                print(f"Successfully connected to SQLite database: {db_file} (SQLite version: {sqlite3.version})")

                # Step 2: Call the table creation helper functions
                print("Checking/creating database schema for tasks, inventory, and parts_to_make...")
                self.create_colors_table()
                self.create_inventory_table()
                self.create_parts_to_make_table()
                self.create_cut_list_table()
                self.create_orders_table()

            except Error as e:
                # Handle any database errors
                print(f"An error occurred during database setup: {e}")
            finally:
                print("Database setup complete.")

    def get_connection(self):
        """Helper to create a fresh connection."""
        # Check Same Thread must be False when using multiprocessing
        # This is a key safety measure for reading data across processes/threads
        return sqlite3.connect(self.db_name, check_same_thread=False)
        
    def create_colors_table(self):
        """Creates a lookup table for colors"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if table exists before creation
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='colors'")
            table_existed = cursor.fetchone() is not None

            sql = """
            CREATE TABLE IF NOT EXISTS colors (
                color_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                hex_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(sql)
            conn.commit()
            print("Table 'colors' checked/created successfully.")
            # load colors from yaml file
            # Check if table exists after creation
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='colors'")
            table_exists_now = cursor.fetchone() is not None
            
            # Determine if table was just created
            was_created = not table_existed and table_exists_now
            
            if was_created:
                print("Table 'colors' was created. Loading initial colors...")
                # Load colors from yaml file only if table was just created
                if os.path.exists(self.colors_file_path):
                    with open(self.colors_file_path, 'r') as f:
                        colors = yaml.safe_load(f)
                        for color in colors['colors']:
                            try:
                                _ = self.add_color(color['name'], color['hex'])
                            except sqlite3.IntegrityError:
                                pass
                    print(f"Loaded colors from {self.colors_file_path}")
                else:
                    print(f"Colors file {self.colors_file_path} not found. No colors loaded.")
            else:
                print("Table 'colors' already existed.")
    
    def create_inventory_min_max(self):
        """Stores the mins and maxes of each item"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS inventory_mm (
                product_id INTEGER PRIMARY KEY,
                item_name TEXT NOT NULL,
                color TEXT NOT NULL,
                min_quantity INT NOT NULL,
                max_quantity INT NOT NULL
            );
            """
            cursor.execute(sql)
            conn.commit()
            print("Table 'shipment' checked/created successfully.")
        
    def create_shipment_table(self):
        """Creates the 'shipment' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS shipment (
                order_id INTEGER PRIMARY KEY,
                goods TEXT NOT NULL,
                customer TEXT NOT NULL,
                address TEXT NOT NULL
            );
            """
            cursor.execute(sql)
            conn.commit()
            print("Table 'shipment' checked/created successfully.")

    def create_inventory_table(self):
        """Creates the 'inventory' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS inventory (
                item_id INTEGER PRIMARY KEY,
                item_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                location TEXT
            );
            """
            cursor.execute(sql)
            conn.commit()
            print("Table 'inventory' checked/created successfully.")

    def create_parts_to_make_table(self):
        """Creates the 'parts_to_make' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS parts_to_make (
                part_id INTEGER PRIMARY KEY,
                part_name TEXT NOT NULL,
                required_count INTEGER NOT NULL,
                due_date TEXT
            );
            """
            cursor.execute(sql)
            conn.commit()
            print("Table 'parts_to_make' checked/created successfully.")

    def create_cut_list_table(self):
        """Creates the 'cut_list' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS cut_list (
                cut_id INTEGER PRIMARY KEY,
                part_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                color INT NOT NULL,
                quantity INTEGER NOT NULL
            );
            """
            cursor.execute(sql)
            conn.commit()
            print("Table 'cut_list' checked/created successfully.")

    def create_orders_table(self):
        """Creates the 'orders' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                order_data TEXT NOT NULL
            );
            """
            cursor.execute(sql)
            conn.commit()
            print("Table 'orders' checked/created successfully.")

    def add_order(self, order_id: int, order_data: dict):
        """Inserts a new order into the orders table.
        returns true if the order is added, false if it already exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if the order already exists
            cursor.execute("SELECT 1 FROM orders WHERE order_id = ?", (order_id,))
            if cursor.fetchone():
                print(f"Order with ID {order_id} already exists. Skipping insert.")
                return False  # Order already exists
            
            # Insert the new order
            sql = "INSERT INTO orders (order_id, order_data) VALUES (?, ?)"
            cursor.execute(sql, (order_id, yaml.dump(order_data)))
            conn.commit()
            print(f"Order with ID {order_id} added successfully.")
            return True  # Order added successfully

    def get_inventory_count(self, name: str, color: str) -> int:
        """
        Queries the inventory table for the total quantity of items matching both the item_name
        and color by searching for both strings within the item_name.
        """
        with self.get_connection() as conn:
            # Use the SQL AND operator to combine both search conditions
            sql = "SELECT SUM(quantity) FROM inventory WHERE item_name LIKE ? AND item_name LIKE ?"
            
            # Prepare the search terms with wildcards for both parameters
            item_search_term = f"%{name}%"
            color_search_term = f"%{color}%"
            
            # Execute the query with a tuple containing both search terms
            cursor = conn.cursor()
            cursor.execute(sql, (item_search_term, color_search_term))
            
            # Return the sum
            result = cursor.fetchone()[0]
            return result if result is not None else 0
    
    def get_min_items(self, name, color):
        """
        Queries the inventory_mm table to check for the numimum quantity that an
        item should have at any given time.
        """
        with self.get_connection() as conn:
            # Use the SQL AND operator to combine both search conditions
            sql = "SELECT min_quantity FROM inventory_mm WHERE item_name LIKE ? AND item_name LIKE ?"
            
            # Prepare the search terms with wildcards for both parameters
            item_search_term = f"%{name}%"
            color_search_term = f"%{color}%"
            
            # Execute the query with a tuple containing both search terms
            cursor = conn.cursor()
            cursor.execute(sql, (item_search_term, color_search_term))
            
            # Return the sum
            result = cursor.fetchone()[0]
            return result if result is not None else 0

    def add_to_cut_list(self, part_name: str, file_path: str, color: str, quantity: int):
        """
        Either insert a new row into the cut_list table or update an existing row by adding to the quantity.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # look up the color int from the colors table by name -- if it does not exist, throw an error
            sql_color_lookup = "SELECT color_id FROM colors WHERE name = ?"
            cursor.execute(sql_color_lookup, (color,))
            color_result = cursor.fetchone()
            if not color_result:
                raise ValueError(f"Color '{color}' not found in colors table. Please add it first.")
            color = color_result[0]

            # Check if the entry already exists
            sql_check = "SELECT quantity FROM cut_list WHERE part_name = ? AND file_path = ? AND color = ?"
            cursor.execute(sql_check, (part_name, file_path, color))
            result = cursor.fetchone()
            
            if result:
                # If it exists, update the quantity
                new_quantity = result[0] + quantity
                sql_update = "UPDATE cut_list SET quantity = ? WHERE part_name = ? AND file_path = ? AND color = ?"
                cursor.execute(sql_update, (new_quantity, part_name, file_path, color))
            else:
                # If it does not exist, insert a new row
                sql_insert = "INSERT INTO cut_list (part_name, file_path, color, quantity) VALUES (?, ?, ?, ?)"
                cursor.execute(sql_insert, (part_name, file_path, color, quantity))
            
            conn.commit()
    
    def add_color(self, name: str, hex_code: str = None) -> int:
        """Adds a new color to the colors table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO colors (name, hex_code) VALUES (?, ?)"
            cursor.execute(sql, (name, hex_code))
            conn.commit()
            return cursor.lastrowid
    
    def get_cut_list(self):
        """
        Retrieves the cut list from the database.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM cut_list;"
            cursor.execute(sql)
            rows = cursor.fetchall()
            # Convert to list of dictionaries for easier handling
            columns = [column[0] for column in cursor.description]
            cut_list = [dict(zip(columns, row)) for row in rows]
            return cut_list

    def remove_from_cut_list(self, cut_id: int, quantity: int = 1):
        """
        Removes an item from the cut list based on its ID and decrements the quantity.
        If the quantity reaches zero, the item is deleted from the table.
        
        Args:
            cut_id (int): The ID of the cut list item to modify
            quantity (int): Amount to decrement (defaults to 1)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check current quantity
            sql_check = "SELECT quantity FROM cut_list WHERE cut_id = ?"
            cursor.execute(sql_check, (cut_id,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"No cut list item found with ID {cut_id}")
            
            current_quantity = result[0]
            new_quantity = current_quantity - quantity
            
            if new_quantity <= 0:
                # Delete the record if quantity would be zero or negative
                sql_delete = "DELETE FROM cut_list WHERE cut_id = ?"
                cursor.execute(sql_delete, (cut_id,))
            else:
                # Update with new quantity
                sql_update = "UPDATE cut_list SET quantity = ? WHERE cut_id = ?"
                cursor.execute(sql_update, (new_quantity, cut_id))
            
            conn.commit()
            print(f"Cut list item with ID {cut_id} updated. New quantity: {new_quantity if new_quantity > 0 else 'Deleted'}")

    def get_full_cut_list_dataframe(self):
        sql_query = """
        SELECT 
            cl.part_name,
            cl.file_path,
            c.name AS color,  -- Using 'color' as the final column name
            cl.quantity
        FROM 
            cut_list cl
        INNER JOIN 
            colors c
        ON 
            cl.color = c.color_id;
        """
        with self.get_connection() as conn:
            # pandas.read_sql will execute this query and return the DataFrame
            df = pd.read_sql(sql_query, conn)
            return df

    def get_unique_colors(self):
        """
        Retrieves a list of unique colors from the colors table.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql_query = """
                SELECT 
                    cl.part_name,
                    cl.file_path,
                    c.name AS color,
                    cl.quantity
                FROM 
                    cut_list cl
                INNER JOIN 
                    colors c
                ON 
                    cl.color = c.color_id;
                """
            df = pd.read_sql(sql_query, conn)
            
            # --- NEW: Get the list of unique colors for the filter ---
            # Ensure all colors are strings and handle potential nulls if necessary
            unique_colors = sorted(df['color'].unique().tolist())
            return unique_colors