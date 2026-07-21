import re
import json
from graph.state import LiveAgentState
from context import mcp_context

async def diagnosis_agent(state: LiveAgentState):
    """Node 1: Evaluates operational database incidents dynamically by calling external MCP tools."""
    print("\n[Node 1] Dynamically diagnosing operational database incident via MCP...")

    # 1. Convert the MCP tools list into a lookup dictionary
    tools = {t.name: t for t in mcp_context.get("tools", [])}

    order_id = state.get("order_id")

    # 2. Invoke 'fetch_order_details' via ainvoke
    if "fetch_order_details" not in tools:
        raise KeyError("Tool 'fetch_order_details' not found in MCP context.")
        
    order_info_str = await tools["fetch_order_details"].ainvoke({"order_id": order_id})
    print(f"   ↳ [MCP Output] {order_info_str}")

    if "not found" in order_info_str.lower() or "error" in order_info_str.lower():
        return {
            "issue": f"ID #{order_id} does not match any active order record or database error occurred.",
            "fix_query": "-- No valid remediation operation can be formulated."
        }

    status_match = re.search(r"Status:\s*([a-zA-Z]+)", order_info_str)
    warehouse_match = re.search(r"Current Warehouse:\s*(\d+)", order_info_str)
    item_match = re.search(r"Item:\s*(.+)$", order_info_str)

    current_status = status_match.group(1) if status_match else "Stuck"
    current_warehouse = int(warehouse_match.group(1)) if warehouse_match else 1
    item_name = item_match.group(1).strip() if item_match else "Premium Shoes"

    # 3. Invoke 'check_item_inventory'
    inventory_str = await tools["check_item_inventory"].ainvoke({"item_name": item_name})
    print(f"   ↳ [MCP Output] {inventory_str}")

    # 4. Invoke 'calculate_sla_deadline'
    sla_str = await tools["calculate_sla_deadline"].ainvoke({"status": current_status})
    print(f"   ↳ [MCP Output] {sla_str}")

    issue = f"Order #{order_id} ('{item_name}') exception found.\n\n" \
            f"📊 Details: {order_info_str}\n" \
            f"📦 Inventory: {inventory_str}\n" \
            f"⏱️ Matrix Rule: {sla_str}"

    alt_warehouses = re.findall(r"Warehouse #(\d+):\s*([1-9]\d*)\s*units", inventory_str)

    valid_alternatives = [w_id for w_id, stock in alt_warehouses if int(w_id) != current_warehouse]

    if valid_alternatives:
        target_wh = valid_alternatives[0]
        proposed_query = f"UPDATE orders SET warehouse_id = {target_wh}, status = 'Ready' WHERE order_id = {order_id};"
        issue += f"\n\n💡 System Recommendation: Route to Warehouse #{target_wh} where available units exist."
    else:
        proposed_query = f"-- No alternative stock tracking found for '{item_name}' globally."
        issue += f"\n\n❌ CRITICAL: Out of stock across all physical enterprise locations."

    return {
        "issue": issue,
        "fix_query": proposed_query
    }