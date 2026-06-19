import sqlite3

def setup_mock_database():
    """Create a local Sqlite database representing an e-commerce platform"""
    conn=sqlite3.connect("company.db")
    cursor=conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS orders;")
    cursor.execute("DROP TABLE IF EXISTS inventory;")

    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_name TEXT,
            status TEXT,
            warehouse_id INTEGER
        );
    """)
    cursor.execute("""
        CREATE TABLE inventory (
            warehouse_id INTEGER,
            item_name TEXT,
            stock_count INTEGER
        );
    """)

    cursor.execute("INSERT INTO orders VALUES (4092, 'Alice Smith', 'Limbo', 1);")
    cursor.execute("INSERT INTO inventory VALUES (1, 'Premium Shoes', 0);")  
    cursor.execute("INSERT INTO inventory VALUES (3, 'Premium Shoes', 15);") 
    
    conn.commit()
    conn.close()
