import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RemediationTools")
DB_PATH = "/tmp/company.db"


@mcp.tool()
def fetch_order_details(order_id: int) -> str:
    """Retrieves e-commerce order details (status, warehouse_id, item_name) by its unique order_id."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT order_id, customer_name, status, warehouse_id, item_name FROM orders WHERE order_id = ?;", (order_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return f"❌ Order ID {order_id} not found in the database."
        
        return f"📦 Order #{row[0]} | Customer: {row[1]} | Status: {row[2]} | Current Warehouse: {row[3]} | Item: {row[4]}"
    except Exception as e:
        return f"❌ Error querying database: {str(e)}"


@mcp.tool()
def check_item_inventory(item_name: str) -> str:
    """Checks the stock counts for a specific item across all warehouses to look for alternative fulfillment spots."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT warehouse_id, stock_count FROM inventory WHERE item_name = ?;", (item_name,))
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return f"❌ No inventory tracking data found for item: '{item_name}'."
        
        results = [f"🏭 Warehouse #{r[0]}: {r[1]} units available" for r in rows]
        return f"Inventory status for '{item_name}':\n" + "\n".join(results)
    except Exception as e:
        return f"❌ Error reading inventory: {str(e)}"



@mcp.tool()
def calculate_sla_deadline(status: str) -> str:
    """Calculates the remaining Service Level Agreement (SLA) resolution time based on incident status."""
    if status == "Stuck":
        return "⏰ CRITICAL SLA: 30 minutes remaining for administrative remediation."
    elif status == "Limbo":
        return "⚠️ HIGH SLA: 2 hours remaining for re-routing."
    else:
        return "✅ STANDARD SLA: 24 hours remaining."
    

@mcp.tool()
def execute_remediation_write(order_id: int, target_warehouse: int) -> str:
    """Executes the database updates to route an order to a new warehouse and deduct inventory count safely."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT item_name FROM orders WHERE order_id = ?;", (order_id,))
        row = cursor.fetchone()
        if not row:
            return f"❌ Order ID {order_id} not found."
        item_name = row[0]
        
        cursor.execute("UPDATE orders SET warehouse_id = ?, status = 'Ready' WHERE order_id = ?;", (target_warehouse, order_id))
        
        cursor.execute("""
            UPDATE inventory 
            SET stock_count = MAX(0, stock_count - 1) 
            WHERE item_name = ? AND warehouse_id = ?;
        """, (item_name, target_warehouse))
        
        conn.commit()
        conn.close()
        return f"✅ Success! Order #{order_id} rerouted to Warehouse #{target_warehouse}. Inventory synchronized."
    except Exception as e:
        return f"❌ Database write operation failed: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")