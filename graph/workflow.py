from langgraph.graph import StateGraph,START,END
from graph.state import LiveAgentState
from langgraph.checkpoint.memory import InMemorySaver
from database.queries import setup_mock_database
from sql_agent.diagnosis import diagnosis_agent
from sql_agent.action_execution import action_execution_node
from sql_agent.human_approval import human_approval_node
from langgraph.types import Command
import uuid

setup_mock_database()
memory=InMemorySaver()

def build_graph():
    graph=StateGraph(LiveAgentState)

    graph.add_node("diagnosis",diagnosis_agent)
    graph.add_node("await_approval",human_approval_node)
    graph.add_node("action_execute",action_execution_node)

    graph.add_edge(START,"diagnosis")
    graph.add_edge("diagnosis","await_approval")
    graph.add_edge("await_approval",END)

    
    return graph.compile(checkpointer=memory)

agent_brain=build_graph()

if __name__=="__main__":

    thread_config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    initial_input = {"order_id": 4092}

    print("--- 🏁 STAGE 1: Starting Workflow Run ---")
    for event in agent_brain.stream(initial_input, thread_config, stream_mode="updates"):
        if "__interrupt__" in event:
           
            interrupted_data = event["__interrupt__"][0].value
            print(f"\n📢 [Backend Interface Event Router]: Sent payload to Slack successfully!\n{interrupted_data}")
            
    print("\n--- ⏸️ Graph is now safely asleep ---")

    
    user_action_input = "approved" 
    print(f"\n--- ▶️ STAGE 2: Human Interaction Triggered ({user_action_input.upper()}) ---")
    
    for event in agent_brain.stream(Command(resume=user_action_input), thread_config, stream_mode="updates"):
        print(event)


