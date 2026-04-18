import sqlite3
from sqlite3 import Error
import os
from dataclasses import dataclass
import yaml
import pandas as pd
from logger import setup_logger

logger = setup_logger()

class MRPDatabase:
    def __init__ (self, db_file_path: str, colors_file_path: str = 'src/colors.yaml'):
        self.db_name = db_file_path
        if not os.path.exists(db_file_path):
            logger.info(f"I did not find a a database file at {db_file_path}. Creating a new database file")
        conn = None
        self.colors_file_path = colors_file_path
        try:
            conn = sqlite3.connect(db_file_path)
            logger.info(f"Successfully connected to the database at {db_file_path}")
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
                logger.info(f"Successfully connected to SQLite database: {db_file} (SQLite version: {sqlite3.version})")

                # Step 2: Call the table creation helper functions
                logger.info("Checking/creating database schema for tasks, inventory, and parts_to_make...")
                self.create_colors_table()
                self.create_inventory_table()
                self.create_parts_to_make_table()
                self.create_jobs_table()
                self.create_finished_goods_table()
                self.create_cut_list_table()
                self.create_orders_table()
                self.create_shipment_table() # Added this line based on the instruction's intent
                self.create_logs_table() # Added this line
                self.update_schema()

            except Error as e:
                # Handle any database errors
                logger.error(f"An error occurred during database setup: {e}")
            finally:
                logger.info("Database setup complete.")

    def get_connection(self):
        """Helper to create a fresh connection."""
        # Check Same Thread must be False when using multiprocessing
        # This is a key safety measure for reading data across processes/threads
        conn = sqlite3.connect(self.db_name, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn
        
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
            logger.info("Table 'colors' checked/created successfully.")
            # load colors from yaml file
            # Check if table exists after creation
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='colors'")
            table_exists_now = cursor.fetchone() is not None
            
            # Determine if table was just created
            was_created = not table_existed and table_exists_now
            
            if was_created:
                logger.info("Table 'colors' was created. Loading initial colors...")
                # Load colors from yaml file only if table was just created
                if os.path.exists(self.colors_file_path):
                    with open(self.colors_file_path, 'r') as f:
                        colors = yaml.safe_load(f)
                        for color in colors['colors']:
                            try:
                                _ = self.add_color(color['name'], color['hex'])
                            except sqlite3.IntegrityError:
                                pass
                    logger.info(f"Loaded colors from {self.colors_file_path}")
                else:
                    logger.warning(f"Colors file {self.colors_file_path} not found. No colors loaded.")
            else:
                logger.info("Table 'colors' already existed.")
    
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
            logger.info("Table 'inventory_mm' checked/created successfully.")
        
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
            logger.info("Table 'shipment' checked/created successfully.")

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
            logger.info("Table 'inventory' checked/created successfully.")

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
            logger.info("Table 'parts_to_make' checked/created successfully.")

    def create_jobs_table(self):
        """Creates the 'jobs' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', -- pending, cut, sewn, complete
                batch_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(sql)
            conn.commit()
            logger.info("Table 'jobs' checked/created successfully.")

    def create_finished_goods_table(self):
        """Creates the 'finished_goods' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS finished_goods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                location TEXT
            );
            """
            cursor.execute(sql)
            conn.commit()
            logger.info("Table 'finished_goods' checked/created successfully.")

    def add_job(self, sku: str, batch_id: str = None) -> int:
        """Adds a new job to the jobs table."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO jobs (sku, batch_id, status) VALUES (?, ?, 'pending')"
            cursor.execute(sql, (sku, batch_id))
            conn.commit()
            return cursor.lastrowid

    def get_jobs(self, status: str = None):
        """Retrieves jobs, optionally filtered by status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                sql = "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC"
                cursor.execute(sql, (status,))
            else:
                sql = "SELECT * FROM jobs ORDER BY created_at DESC"
                cursor.execute(sql)
            
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            jobs = [dict(zip(columns, row)) for row in rows]
            return jobs

    def update_job_status(self, job_id: int, status: str):
        """Updates the status of a job."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "UPDATE jobs SET status = ? WHERE job_id = ?"
            cursor.execute(sql, (status, job_id))
            conn.commit()
            logger.info(f"Job {job_id} status updated to {status}.")

    def add_finished_goods(self, sku: str, quantity: int, location: str = 'Default'):
        """Adds finished goods to inventory."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO finished_goods (sku, quantity, location) VALUES (?, ?, ?)"
            cursor.execute(sql, (sku, quantity, location))
            conn.commit()
            logger.info(f"Added {quantity} of {sku} to finished goods.")

    def get_finished_goods_count(self, sku: str) -> int:
        """Gets total quantity of a finished good sku."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT SUM(quantity) FROM finished_goods WHERE sku = ?"
            cursor.execute(sql, (sku,))
            result = cursor.fetchone()[0]
            return result if result is not None else 0

    def get_all_finished_goods(self):
        """Retrieves all finished goods aggregated by SKU."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT sku, SUM(quantity) as quantity FROM finished_goods GROUP BY sku ORDER BY sku"
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [{'sku': row[0], 'quantity': row[1]} for row in rows]

    def get_job(self, job_id: int):
        """Retrieves a single job by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT * FROM jobs WHERE job_id = ?"
            cursor.execute(sql, (job_id,))
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
            return None

    def create_cut_list_table(self):
        """Creates the 'cut_list' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS cut_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                panel_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                color TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(panel_name, file_path, color, status)
            );
            """
            cursor.execute(sql)
            conn.commit()
            logger.info("Table 'cut_list' checked/created successfully.")

    def add_cut_item(self, panel_name: str, file_path: str, color: str, quantity: int = 1):
        """
        Adds a cut item to the cut_list. 
        If an identical pending item exists, increments the quantity.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Upsert logic: SQLite >= 3.24 supports ON CONFLICT DO UPDATE
            # But let's be safe with basic logic: Check then Insert/Update
            sql_check = "SELECT id, quantity FROM cut_list WHERE panel_name = ? AND file_path = ? AND color = ? AND status = 'pending'"
            cursor.execute(sql_check, (panel_name, file_path, color))
            result = cursor.fetchone()
            
            if result:
                new_qty = result[1] + quantity
                sql_update = "UPDATE cut_list SET quantity = ? WHERE id = ?"
                cursor.execute(sql_update, (new_qty, result[0]))
                logger.info(f"Updated cut item {panel_name} ({color}): {result[1]} -> {new_qty}")
            else:
                sql_insert = "INSERT INTO cut_list (panel_name, file_path, color, quantity) VALUES (?, ?, ?, ?)"
                cursor.execute(sql_insert, (panel_name, file_path, color, quantity))
                logger.info(f"Inserted new cut item {panel_name} ({color}) x{quantity}")
            
            conn.commit()

    def get_cut_list(self, color: str = None):
        """Retrieves pending cut items, optionally filtered by color."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if color and color != 'ALL':
                sql = "SELECT * FROM cut_list WHERE status = 'pending' AND color = ? ORDER BY panel_name, color"
                cursor.execute(sql, (color,))
            else:
                sql = "SELECT * FROM cut_list WHERE status = 'pending' ORDER BY panel_name, color"
                cursor.execute(sql)
            
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def get_pending_cut_colors(self):
        """Retrieves a list of distinct colors from the pending cut list."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT DISTINCT color FROM cut_list WHERE status = 'pending' ORDER BY color"
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def update_cut_item_status(self, cut_id: int, status: str):
        """Update status of a single cut_list item."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "UPDATE cut_list SET status = ? WHERE id = ?"
            cursor.execute(sql, (status, cut_id))
            conn.commit()
            logger.info(f"Cut item {cut_id} status updated to '{status}'.")

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
            logger.info("Table 'orders' checked/created successfully.")

    def add_order(self, order_id: int, order_data: dict):
        """Inserts a new order into the orders table.
        returns true if the order is added, false if it already exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Check if the order already exists
            cursor.execute("SELECT 1 FROM orders WHERE order_id = ?", (order_id,))
            if cursor.fetchone():
                logger.info(f"Order with ID {order_id} already exists. Skipping insert.")
                return False  # Order already exists
            
            # Insert the new order
            sql = "INSERT INTO orders (order_id, order_data) VALUES (?, ?)"
            cursor.execute(sql, (order_id, yaml.dump(order_data)))
            conn.commit()
            logger.info(f"Order with ID {order_id} added successfully.")
            return True  # Order added successfully

    def get_all_orders(self, limit: int = 100):
        """
        Retrieves all orders from the database, parsing the YAML data.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT order_id, order_data FROM orders ORDER BY order_id DESC LIMIT ?"
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            
            orders = []
            for row in rows:
                try:
                    order_data = yaml.safe_load(row[1])
                    # Ensure order_id is in the data dict if not already
                    if 'id' not in order_data:
                        order_data['id'] = row[0]
                    orders.append(order_data)
                except yaml.YAMLError as e:
                    logger.error(f"Error parsing YAML for order {row[0]}: {e}")
                    # Provide partial data if parsing fails
                    orders.append({'id': row[0], 'name': 'Error Loading Data', 'error': str(e)})
                    
            return orders

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


    
    def add_color(self, name: str, hex_code: str = None) -> int:
        """Adds a new color to the colors table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "INSERT INTO colors (name, hex_code) VALUES (?, ?)"
            cursor.execute(sql, (name, hex_code))
            conn.commit()
            return cursor.lastrowid
    
    def get_color_name(self, color_id: int) -> str:
        """
        Retrieves the name of a color given its ID.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT name FROM colors WHERE color_id = ?"
            cursor.execute(sql, (color_id,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return "Unknown"
    


    def update_schema(self):
        """
        Checks for missing columns in existing tables and adds them if necessary.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # No updates needed currently
            pass





    def create_logs_table(self):
        """Creates the 'logs' table if it does not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                level TEXT,
                module TEXT,
                message TEXT
            );
            """
            cursor.execute(sql)
            conn.commit()
            logger.info("Table 'logs' checked/created successfully.")

    def insert_log(self, timestamp: str, level: str, module: str, message: str):
        """Inserts a new log record into the logs table."""
        try:
            # Use specific connection to avoid threading issues
            with self.get_connection() as conn:
                cursor = conn.cursor()
                sql = 'INSERT INTO logs(timestamp, level, module, message) VALUES(?,?,?,?)'
                cursor.execute(sql, (timestamp, level, module, message))
                conn.commit()
        except Error as e:
            # Fallback to console print if DB logging fails to avoid infinite recursion
            print(f"Failed to insert log into DB: {e}")

    def get_logs(self, limit: int = 100, level: str = None, module: str = None):
        """Retrieves logs with optional filtering."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM logs WHERE 1=1"
                params = []
                
                if level and level != 'ALL':
                    query += " AND level = ?"
                    params.append(level)
                
                if module and module != 'ALL':
                    query += " AND module = ?"
                    params.append(module)
                    
                query += " ORDER BY id DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, tuple(params))
                return cursor.fetchall()
        except Error as e:
            logger.error(f"Error retrieving logs: {e}")
            return []