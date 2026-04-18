import pytest
import sqlite3
import os
import time
import sys
# Ensure src is in path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_connector import MRPDatabase
from logger import setup_logger

# Need to make sure we use a test DB file
TEST_DB = 'test_web_logging.db'

@pytest.fixture
def db():
    # Remove existing test db
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    # Initialize DB (creates tables including logs)
    database = MRPDatabase(TEST_DB)
    
    # Setup logger to use this DB (hacky since setup_logger uses global or internal config)
    # But since we modified logger.py to default to inventory.db, we might need to patch it 
    # OR simpler: just test the db_connector logic directly for now, 
    # and separately test that logger works
    
    yield database
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_logs_table_creation(db):
    """Test that logs table exists"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'logs'

def test_insert_and_retrieve_log(db):
    """Test inserting and retrieving logs manually"""
    ts = "2023-10-27 10:00:00"
    db.insert_log(ts, "INFO", "test_module", "Test message")
    
    logs = db.get_logs()
    assert len(logs) == 1
    assert logs[0][1] == ts
    assert logs[0][2] == "INFO"
    assert logs[0][3] == "test_module"
    assert logs[0][4] == "Test message"

def test_log_filtering(db):
    """Test filtering logs"""
    db.insert_log("2023-10-27 10:00:00", "INFO", "mod1", "Msg 1")
    db.insert_log("2023-10-27 10:01:00", "ERROR", "mod1", "Msg 2")
    db.insert_log("2023-10-27 10:02:00", "INFO", "mod2", "Msg 3")
    
    # Filter by module
    mod1_logs = db.get_logs(module="mod1")
    assert len(mod1_logs) == 2
    
    # Filter by level
    error_logs = db.get_logs(level="ERROR")
    assert len(error_logs) == 1
    assert error_logs[0][4] == "Msg 2"
    
    # Filter by both
    mod2_info = db.get_logs(module="mod2", level="INFO")
    assert len(mod2_info) == 1
    
    # No match
    no_match = db.get_logs(module="mod2", level="ERROR")
    assert len(no_match) == 0

