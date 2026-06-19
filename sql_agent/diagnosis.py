from graph.state import LiveAgentState
import sqlite3

def diagnosis_agent(state: LiveAgentState):
    """Node 1: Evaluates operational database incidents dynamically based on order schema."""
    print("\n🔍 [Node 1] Dynamically diagnosing operational database incident...")

    order_id = state.get("order_id")


    conn = sqlite3.connect("/data/company.db")
    cursor = conn.cursor()

    cursor.execute("SELECT status, warehouse_id, item_name FROM orders WHERE order_id = ?", (order_id,))
    order = cursor.fetchone()

    if order is None:
        issue = f"ID #{order_id} does not match any active order record. This tool is strictly for order incident remediation."
        proposed_query = "-- No valid remediation operation can be formulated."
        conn.close()
    else:
        current_status, current_warehouse, item_name = order
        

        cursor.execute("""
            SELECT warehouse_id, stock_count 
            FROM inventory 
            WHERE item_name = ? AND stock_count > 0 AND warehouse_id != ?
            LIMIT 1
        """, (item_name, current_warehouse))

        alternative = cursor.fetchone()
        conn.close()
        

        issue = f"Order #{order_id} ('{item_name}') is stuck in '{current_status}' status at Warehouse {current_warehouse} due to 0 inventory."
        
        if alternative:
            proposed_query = f"UPDATE orders SET warehouse_id = {alternative[0]}, status = 'Ready' WHERE order_id = {order_id};"
            issue += f" Found alternative stock at Warehouse {alternative[0]}."
        else:
            proposed_query = f"-- No alternative stock found for '{item_name}' in any other warehouse."
            issue += f" CRITICAL: Out of stock globally for '{item_name}'."

    print(f"   ↳ Incident Diagnosis: {issue}")
    print(f"   ↳ Remediation Query: {proposed_query}")

    return {
        "issue": issue,
        "fix_query": proposed_query
    }