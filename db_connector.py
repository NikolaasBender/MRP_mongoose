import sqlite3
from sqlite3 import Error
import os


class MRPDatabase:
    def __init__ (self, db_file_path: str):
        if not os.path.exists(db_file_path):
            print(f"I did not find a a database file at {db_file_path}\nCreating a new database file")
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_file_path)
            print(f"Successfully connected to the database at {db_file_path}")
        except:
            raise ValueError("Cant connect to database")
        
    def create_shipment_table(self):
        """Creates the 'shipment' table if it does not exist."""
        cursor = self.conn.cursor()
        sql = """
        CREATE TABLE IF NOT EXISTS shipment (
            order_id INTEGER PRIMARY KEY,
            goods TEXT NOT NULL,
            customer TEXT NOT NULL,
            address TEXT NOT NULL
        );
        """
        cursor.execute(sql)
        self.conn.commit()
        print("Table 'shipment' checked/created successfully.")

    def create_inventory_table(self):
        """Creates the 'inventory' table if it does not exist."""
        cursor = self.conn.cursor()
        sql = """
        CREATE TABLE IF NOT EXISTS inventory (
            item_id INTEGER PRIMARY KEY,
            item_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            location TEXT
        );
        """
        cursor.execute(sql)
        self.conn.commit()
        print("Table 'inventory' checked/created successfully.")

    def create_parts_to_make_table(self):
        """Creates the 'parts_to_make' table if it does not exist."""
        cursor = self.conn.cursor()
        sql = """
        CREATE TABLE IF NOT EXISTS parts_to_make (
            part_id INTEGER PRIMARY KEY,
            part_name TEXT NOT NULL,
            required_count INTEGER NOT NULL,
            due_date TEXT
        );
        """
        cursor.execute(sql)
        self.conn.commit()
        print("Table 'parts_to_make' checked/created successfully.")

    # --- Main Setup Function ---

    def setup_database(self, db_file: str):
        """
        Creates a connection to the SQLite database file specified by db_file.
        If the file does not exist, it is created.

        After connecting, it calls helper functions to create the 'tasks',
        'inventory', and 'parts_to_make' tables if they don't already exist.

        Args:
            db_file (str): The name and path of the database file (e.g., 'my_project.db').
        """
        conn = None
        try:
            # Step 1: Connect to the database. This creates the file if it doesn't exist.
            conn = sqlite3.connect(db_file)
            print(f"Successfully connected to SQLite database: {db_file} (SQLite version: {sqlite3.version})")

            # Step 2: Call the table creation helper functions
            print("Checking/creating database schema for tasks, inventory, and parts_to_make...")
            self.create_inventory_table(conn)
            self.create_parts_to_make_table(conn)

        except Error as e:
            # Handle any database errors
            print(f"An error occurred during database setup: {e}")
        finally:
            # Step 3: Always ensure the connection is closed
            if conn:
                conn.close()
                print("Database connection closed.")


# --- Example Usage ---
if __name__ == '__main__':
    # Define the name of your database file
    db_name = "my_project_data.db"

    db_man = MRPDatabase(db_name)

    # Call the function to set up the database and table
    db_man.setup_database()

    print("-" * 30)

    # Optional: Run the function again to demonstrate that the table is not recreated
    print("Running setup_database again (should not error and tables won't be recreated):")
    db_man.setup_database()
