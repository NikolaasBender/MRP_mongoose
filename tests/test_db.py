import pytest
import sqlite3
from sqlite3 import Error
from datetime import datetime

# --- DATABASE SETUP HELPERS (REQUIRED FOR FIXTURE) ---

def create_tasks_table(conn: sqlite3.Connection):
    """Creates the 'tasks' table if it does not exist."""
    conn.cursor().execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        priority INTEGER,
        status INTEGER DEFAULT 0
    );
    """)
    conn.commit()

def create_inventory_table(conn: sqlite3.Connection):
    """Creates the 'inventory' table if it does not exist."""
    conn.cursor().execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_id INTEGER PRIMARY KEY,
        item_name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        location TEXT
    );
    """)
    conn.commit()

def create_shipments_table(conn: sqlite3.Connection):
    """Creates the 'shipments' table if it does not exist."""
    conn.cursor().execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        shipment_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        shipment_date TEXT
    );
    """)
    conn.commit()

# Note: The 'parts_to_make' table creation is omitted here for brevity 
# but can be added in the same way.

# --- DATA MANIPULATION FUNCTIONS (Simplified for Testing) ---

def insert_shipment(conn: sqlite3.Connection, product_name: str, shipment_date: str):
    """Inserts a new shipment record into the shipments table."""
    sql = 'INSERT INTO shipments(product_name, shipment_date) VALUES(?,?)'
    cursor = conn.cursor()
    cursor.execute(sql, (product_name, shipment_date))
    conn.commit()
    return cursor.lastrowid

def select_shipment_by_id(conn: sqlite3.Connection, shipment_id: int):
    """Selects a shipment record by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM shipments WHERE shipment_id=?", (shipment_id,))
    return cursor.fetchone()

# --- PYTEST FIXTURE ---

@pytest.fixture(scope="function")
def db_connection():
    """
    Creates a new isolated, in-memory SQLite database for each test function.
    
    The ':memory:' database is destroyed automatically when the connection is closed.
    """
    print("\n[SETUP] Creating in-memory database.")
    # Use ':memory:' for an in-memory database that never touches the disk.
    conn = sqlite3.connect(":memory:") 
    
    # Setup the tables required for testing
    create_tasks_table(conn)
    create_inventory_table(conn)
    create_shipments_table(conn)
    
    yield conn  # The test runs here, receiving the connection object.
    
    print("[TEARDOWN] Closing in-memory database connection.")
    conn.close()

# --- PYTEST TEST CASES ---

def test_database_is_in_memory(db_connection):
    """Verify that the database is in memory and not a file on disk."""
    # If the database is in memory, the database property will be ':memory:'
    assert db_connection.database == ':memory:'

def test_shipment_table_creation(db_connection):
    """Test that the shipments table was correctly created by the fixture."""
    cursor = db_connection.cursor()
    # Attempt to read from the table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shipments'")
    result = cursor.fetchone()
    assert result is not None
    assert result[0] == 'shipments'

def test_insert_and_retrieve_shipment(db_connection):
    """Test the insertion and retrieval of a shipment record."""
    product = "Super Widget Pro"
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Insert the data
    shipment_id = insert_shipment(db_connection, product, date_str)
    
    # 2. Assert insertion was successful
    assert shipment_id is not None
    
    # 3. Retrieve the data
    retrieved_shipment = select_shipment_by_id(db_connection, shipment_id)
    
    # 4. Assert the retrieved data matches
    assert retrieved_shipment is not None
    assert retrieved_shipment[0] == shipment_id
    assert retrieved_shipment[1] == product
    assert retrieved_shipment[2] == date_str

def test_initial_inventory_is_empty(db_connection):
    """Test that the inventory table starts with zero rows."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventory")
    count = cursor.fetchone()[0]
    assert count == 0
