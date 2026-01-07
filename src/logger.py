import logging
import sys

# Define a custom handler to write to DB
class DBHandler(logging.Handler):
    def __init__(self, database_file='inventory.db'):
        super().__init__()
        self.db_file = database_file
        # We perform lazy connection or just connect on emit
        # Ideally, we should use a connection pool or shared connection, 
        # but for logging simplicity we'll re-use the connector logic if possible
        # Or import the connector. 
        # CAUTION: Importing db_connector here might cause circular imports if db_connector imports logger.
        # To avoid circular import, we will do a local import inside emit.

    def emit(self, record):
        try:
            # Avoid circular import by importing here
            # Also we need to be careful about recursion if db_connector logs something
            from db_connector import MRPDatabase
            
            # Format timestamp
            # record.created is float, we want formatted string
            import datetime
            ts = datetime.datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
            
            # We create a fresh connection or use a localized one to insure thread safety
            # But creating a new MRPDatabase object for every log is expensive.
            # Ideally we pass the db instance to the logger, but logger is global.
            # Let's try to adapt the db_connector to allow quick connection or just direct sqlite3 here.
            import sqlite3
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            sql = 'INSERT INTO logs(timestamp, level, module, message) VALUES(?,?,?,?)'
            cursor.execute(sql, (ts, record.levelname, record.module, record.getMessage()))
            conn.commit()
            conn.close()
        except Exception as e:
            # If DB logging fails, fallback to stderr just in case, but don't crash
            sys.stderr.write(f"Failed to log to DB: {e}\n")

def setup_logger(name=None):
    """
    Configures and returns a logger with a standard format.
    If name is provided, returns a child logger.
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured to avoid duplicate handlers
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # Capture all logs, handlers will filter
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add console handler
        logger.addHandler(console_handler)
        
        # Add DB Handler
        try:
            db_handler = DBHandler()
            db_handler.setLevel(logging.INFO) # Log info and above to DB
            logger.addHandler(db_handler)
        except Exception as e:
            print(f"Failed to setup DB logging: {e}")
            
    return logger
