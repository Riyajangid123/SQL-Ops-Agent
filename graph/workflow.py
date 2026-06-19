import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from graph.state import LiveAgentState
from sql_agent.diagnosis import diagnosis_agent
from sql_agent.action_execution import action_execution_node
from sql_agent.human_approval import human_approval_node

memory = InMemorySaver()

def build_graph():
    
    graph = StateGraph(LiveAgentState)


    graph.add_node("diagnosis", diagnosis_agent)
    graph.add_node("await_approval", human_approval_node)
    graph.add_node("action_execute", action_execution_node)


    graph.add_edge(START, "diagnosis")
    graph.add_edge("diagnosis", "await_approval")
    
    
    graph.add_edge("await_approval", "action_execute")
    graph.add_edge("action_execute", END)

    
    return graph.compile(checkpointer=memory)


agent_brain = build_graph()