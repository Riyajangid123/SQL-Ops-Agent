from graph.state import LiveAgentState
import sqlite3 

def action_execution_node(state:LiveAgentState):
    """Node 3: Executes write actions conditionally based on approval output."""
    print("\n⚡ [Node 3] Evaluating user response...")

    if state["status"]=="approved":
        print("   ↳ Execution Approved! Writing mutations directly to SQL...")
        conn = sqlite3.connect("/data/company.db")
        cursor = conn.cursor()
        cursor.execute(state["fix_query"])
        conn.commit()

        cursor.execute("SELECT status, warehouse_id FROM orders WHERE order_id = ?", (state["order_id"],))
        updated_order = cursor.fetchone()
        conn.close()
        print(f"   ↳ SUCCESS: Database Updated! New Order State: {updated_order}")
    else:
        print("   ↳ Execution REJECTED by human supervisor. Aborting operation cleanly.")
        
    return {}