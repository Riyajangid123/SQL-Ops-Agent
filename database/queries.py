import sqlite3

def setup_mock_database():
    """Creates a local SQLite database representing an e-commerce platform inside /tmp."""
    
    print("🗄️ [Setup Script] Spawning standalone database build sequence at /tmp/company.db...")
    conn = sqlite3.connect("/tmp/company.db")
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
            ('Premium Shoes', 1, 0),   -- Out of stock at current location
            ('Premium Shoes', 2, 50),  -- Alternative location has stock
            ('Premium Shoes', 3, 10),  
            
            ('Wireless Headphones', 2, 0),  -- Out of stock at current location
            ('Wireless Headphones', 1, 35)  -- Alternative location has stock
    """)
    
    conn.commit()
    conn.close()
    print("✅ [Setup Script] Database build completed successfully.")

if __name__ == "__main__":
    setup_mock_database()