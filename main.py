import os
import json
import asyncio
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from langgraph.types import Command
from langgraph.errors import GraphInterrupt
from graph.workflow import agent_brain 

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import convert_mcp_to_langchain_tools


mcp_context = {}

from langchain_mcp_adapters.tools import load_mcp_tools

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the application lifecycle and mounts the local Python MCP server context."""
    print("\n⚙️ [Lifespan] Initializing system environments...")

    print("🔌 [Lifespan] Establishing Model Context Protocol (MCP) client tunnel...")
    try:
        server_params = StdioServerParameters(
            command="python",       
            args=["mcp_server.py"]  
        )
        
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:

                await session.initialize()
                print("⚡ [Lifespan] MCP Session Handshake completed successfully.")
                
                langchain_mcp_tools = await load_mcp_tools(session)
                mcp_context["tools"] = langchain_mcp_tools
                print(f"📦 [Lifespan] Successfully bound {len(langchain_mcp_tools)} remote MCP tools.")
                
                yield
                
    except Exception as mcp_err:
        print(f"⚠️ [Lifespan] MCP setup failed: {str(mcp_err)}")
        mcp_context["tools"] = []
        yield

app = FastAPI(lifespan=lifespan)

slack_app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
handler = AsyncSlackRequestHandler(slack_app)

@slack_app.event("app_mention")
async def handle_initial_mention(event, say):
    """Catches initial user request from Slack, updates graph state variables, and watches for native interrupts."""
    user_text = event.get("text")
    thread_ts = event.get("ts") 
    user_question = user_text.split(">")[-1].strip()

    order_id_match = re.search(r'\b\d+\b', user_question)
    
    if not order_id_match:
        await say(text="❌ *Error:* Please include a valid Order ID number so I can check the database records.", thread_ts=thread_ts)
        return

    dynamic_order_id = int(order_id_match.group())
    thread_config = {"configurable": {"thread_id": thread_ts}}
    
    
    initial_input = {
        "order_id": dynamic_order_id,
        "user_query": user_question
    }

    await say(text=f"⚙️ *Consulting LangGraph State Machine for Order #{dynamic_order_id}...*", thread_ts=thread_ts)

    try:
        async for event_update in agent_brain.astream(initial_input, thread_config, stream_mode="updates"):
            if "action_execute" in event_update:
                await say(text="🎯 *Operation completed successfully on the database layer.*", thread_ts=thread_ts)

        current_state = await agent_brain.aget_state(thread_config)
        
        if current_state.next and current_state.tasks and current_state.tasks[0].interrupts:
            state_data = current_state.values
            
            system_issue = state_data.get("issue", "Administrative intervention required.")
            pending_sql = state_data.get("fix_query", "No mutation query found.")
            
            interactive_blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"🚨 *AI Administrative Intervention Request*\n\n*Issue Identified:*\n>{system_issue}\n\n*Proposed Mutation Query:*\n`{pending_sql}`"}
                },
                {
                    "type": "actions",
                    "block_id": f"approval_block_{thread_ts}", 
                    "elements": [
                        {"type": "button", "text": {"type": "plain_text", "text": "Approve ✅"}, "style": "primary", "action_id": "approve_action"},
                        {"type": "button", "text": {"type": "plain_text", "text": "Reject ❌"}, "style": "danger", "action_id": "reject_action"}
                    ]
                }
            ]
            
            await slack_app.client.chat_postMessage(
                channel=event.get("channel"),
                blocks=interactive_blocks,
                thread_ts=thread_ts
            )

    except Exception as err:
        await say(text=f"❌ *System Error:* `{str(err)}`", thread_ts=thread_ts)

@slack_app.action("approve_action")
async def handle_slack_approval_button(ack, body, say):
    """Catches approval click, updates the native interrupt value, and kicks off Node 3 execution."""
    await ack() 
    
    block_id = body["actions"][0]["block_id"]
    thread_id = block_id.split("approval_block_")[-1]
    thread_config = {"configurable": {"thread_id": thread_id}}
    
    await say(text="🚀 *Approval received! Resuming LangGraph execution context...*", thread_ts=thread_id)
    
    async for event_update in agent_brain.astream(Command(resume="approved"), thread_config, stream_mode="updates"):
        pass
    
    await say(text="🎯 *Database successfully synchronized!*", thread_ts=thread_id)

@slack_app.action("reject_action")
async def handle_slack_rejection_button(ack, body, say):
    """Catches rejection click and safely alerts the graph to abort modifications."""
    await ack()
    block_id = body["actions"][0]["block_id"]
    thread_id = block_id.split("approval_block_")[-1]
    thread_config = {"configurable": {"thread_id": thread_id}}
    
    await say(text="🛑 *Operation rejected by human supervisor. Aborting operation cleanly.*", thread_ts=thread_id)
    
    async for event_update in agent_brain.astream(Command(resume="rejected"), thread_config, stream_mode="whitespaces"):
        pass

@app.post("/slack/events")
async def slack_events_endpoint(request: Request):
    body_bytes = await request.body()
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        payload = {}

    if payload.get("type") == "url_verification":
        return PlainTextResponse(content=payload.get("challenge"))

    return await handler.handle(request)