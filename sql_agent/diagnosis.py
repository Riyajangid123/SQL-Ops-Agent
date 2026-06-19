from graph.state import LiveAgentState
import sqlite3

def diagnosis_agent(state: LiveAgentState):
    """Node 1: Evaluates operational database incidents for stuck orders."""
    print("\n🔍 [Node 1] Diagnosing operational database incident...")

    order_id = state.get("order_id")

    conn = sqlite3.connect("company.db")
    cursor = conn.cursor()

    # Verify if this is an existing operational order issue
    cursor.execute("SELECT status, warehouse_id from orders where order_id=?", (order_id,))
    order = cursor.fetchone()

    if order is None:
        issue = f"ID #{order_id} does not match any active order record. This tool is strictly for order incident remediation."
        proposed_query = "-- No valid remediation operation can be formulated."
        conn.close()
    else:
        # Trace stuck status dependencies
        cursor.execute("SELECT warehouse_id, stock_count FROM inventory WHERE item_name = 'Premium Shoes' AND stock_count > 0")
        alternative = cursor.fetchone()
        conn.close()
        
        issue = f"Order #{order_id} is stuck in '{order[0]}' status at Warehouse {order[1]} due to 0 inventory."
        proposed_query = f"UPDATE orders SET warehouse_id = {alternative[0] if alternative else order[1]}, status = 'Ready' WHERE order_id = {order_id};"

    print(f"   ↳ Incident Diagnosis: {issue}")
    print(f"   ↳ Remediation Query: {proposed_query}")

    return {
        "issue": issue,
        "fix_query": proposed_query
    }