from typing import TypedDict

class LiveAgentState(TypedDict):
    order_id: int
    channel_id: str
    thread_t: str
    issue: str
    fix_query: str
    status: str