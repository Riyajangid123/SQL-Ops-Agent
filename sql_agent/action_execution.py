from graph.state import LiveAgentState
import sqlite3 

def action_execution_node(state: LiveAgentState):
    """Node 3: Executes write actions conditionally and updates inventory quantities."""
    print("\n⚡ [Node 3] Evaluating user response...")

    human_choice = state.get("human_decision") or state.get("status")

    if human_choice == "approved":
        print("   ↳ Execution Approved! Writing mutations directly to SQL...")
    
        conn = sqlite3.connect("/tmp/company.db")
        cursor = conn.cursor()
        
        order_id = state["order_id"]
        cursor.execute("SELECT item_name FROM orders WHERE order_id = ?", (order_id,))
        item_row = cursor.fetchone()
        
        cursor.execute(state["fix_query"])
        
        import re
        warehouse_match = re.search(r"warehouse_id\s*=\s*(\d+)", state["fix_query"])
        
        if warehouse_match and item_row:
            target_warehouse = int(warehouse_match.group(1))
            item_name = item_row[0]
            
            cursor.execute("""
                UPDATE inventory 
                SET stock_count = MAX(0, stock_count - 1) 
                WHERE item_name = ? AND warehouse_id = ?
            """, (item_name, target_warehouse))
            print(f"📦 [Node 3] Deducted 1 unit of '{item_name}' from Warehouse {target_warehouse}.")

        conn.commit()

        cursor.execute("SELECT status, warehouse_id FROM orders WHERE order_id = ?", (order_id,))
        updated_order = cursor.fetchone()
        conn.close()
        
        print(f"   ↳ SUCCESS: Database Updated! New Order State: {updated_order}")
        return {"action_execute": True}
        
    else:
        print(f"   ↳ Execution REJECTED or ABORTED. Aborting operation cleanly.")
        return {"action_execute": False}