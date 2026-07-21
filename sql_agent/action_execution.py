import re
from graph.state import LiveAgentState

async def action_execution_node(state: LiveAgentState):
    """Node 3: Executes write actions safely by delegating everything to the MCP Tool Server."""
    print("\n⚡ [Node 3] Evaluating user response and modifying backend context...")

    from main import mcp_context

    human_choice = state.get("human_decision") or state.get("status")

    if human_choice == "approved":
        print("   ↳ Execution Approved! Triggering mutation tool on MCP Server...")
        
        order_id = state["order_id"]
        
        warehouse_match = re.search(r"warehouse_id\s*=\s*(\d+)", state["fix_query"])
        target_warehouse = int(warehouse_match.group(1)) if warehouse_match else None
        
        if not target_warehouse:
            print("   ↳ Aborted: Could not determine valid target warehouse from state context.")
            return {"action_execute": False}

        # 1. Map tools list into a dictionary lookup by name
        tools = {t.name: t for t in mcp_context.get("tools", [])}

        if "execute_remediation_write" not in tools:
            raise KeyError("Tool 'execute_remediation_write' not found in MCP context.")

        # 2. Asynchronously invoke tool via LangChain interface
        mcp_result = await tools["execute_remediation_write"].ainvoke({
            "order_id": order_id, 
            "target_warehouse": target_warehouse
        })
        
        print(f"   ↳ [MCP Server Feedback] {mcp_result}")
        return {"action_execute": True}
        
    else:
        print("   ↳ Execution REJECTED or ABORTED. Safely terminating graph state.")
        return {"action_execute": False}