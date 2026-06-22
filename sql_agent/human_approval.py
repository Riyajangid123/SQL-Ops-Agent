from graph.state import LiveAgentState
from langgraph.types import interrupt

def human_approval_node(state: LiveAgentState):
    """Node 2: Pauses execution using LangGraph's native interrupt feature."""
    print("\n⏳ [Node 2] Pausing execution! Exposing approval options to human controller...")

    approval_payload = {
        "title": "🚨 AI Administrative Intervention Request",
        "description": state["issue"],
        "proposed_action": state["fix_query"]
    }

    user_choice = interrupt(approval_payload)
    return {"status": user_choice}