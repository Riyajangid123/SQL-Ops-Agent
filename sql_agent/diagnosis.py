from graph.state import LiveAgentState
import sqlite3

def diagnosis_agent(state:LiveAgentState):
    """Node 1: Connects to SQL, finds the problem, and structures a fix."""
    print("\n🔍 [Node 1] Diagnosing the database problem...")

    order_id=state["order_id"]

    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()

    cursor.execute("SELECT status,warehouse_id from orders where order_id=?",(order_id,))
    order = cursor.fetchone()

    cursor.execute("SELECT warehouse_id, stock_count FROM inventory WHERE item_name = 'Premium Shoes' AND stock_count > 0")
    alternative = cursor.fetchone()
    conn.close()

    issue = f"Order #{order_id} is stuck in '{order[0]}' status at Warehouse {order[1]} due to 0 inventory."
    proposed_query = f"UPDATE orders SET warehouse_id = {alternative[0]}, status = 'Ready' WHERE order_id = {order_id};"
    
    print(f"   ↳ System Found Issue: {issue}")
    print(f"   ↳ Formulated Query: {proposed_query}")

    return {
        "issue":issue,
        "fix_query":proposed_query
    }

