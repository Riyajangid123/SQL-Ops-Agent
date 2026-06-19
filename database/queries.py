import sqlite3

def setup_mock_database():
    """Create a local Sqlite database representing an e-commerce platform"""

    conn = sqlite3.connect("/data/company.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS orders;")
    cursor.execute("DROP TABLE IF EXISTS inventory;")

    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_name TEXT,
            status TEXT,
            warehouse_id INTEGER,
            item_name TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE inventory (
            warehouse_id INTEGER,
            item_name TEXT,
            stock_count INTEGER
        );
    """)

    cursor.execute("INSERT INTO orders VALUES (4092, 'Alice Smith', 'Limbo', 1, 'Premium Shoes');")
    
    cursor.execute("""
        INSERT OR IGNORE INTO orders (order_id, status, warehouse_id, item_name) 
        VALUES 
            (1001, 'Stuck', 1, 'Premium Shoes'),
            (1002, 'Stuck', 2, 'Wireless Headphones'),
            (1003, 'Processing', 1, 'Premium Shoes'),
            (1004, 'Stuck', 3, 'Wireless Headphones');
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO inventory (item_name, warehouse_id, stock_count)
        VALUES 
            ('Premium Shoes', 1, 0),   -- Out of stock
            ('Premium Shoes', 2, 50),  -- Stock available
            ('Premium Shoes', 3, 10),  -- Stock available
            
            ('Wireless Headphones', 2, 0),  -- Out of stock
            ('Wireless Headphones', 1, 35)  -- Stock available
    """)
    
    conn.commit()
    conn.close()