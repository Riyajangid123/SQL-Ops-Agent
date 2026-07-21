import os
import json
import asyncio
import re
import sqlite3
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

from langgraph.types import Command
from langgraph.errors import GraphInterrupt
from graph.workflow import agent_brain
from context import mcp_context
from langchain_mcp_adapters.client import MultiServerMCPClient


MCP_CONFIG = {
    "remediation_server": {
        "transport": "stdio",
        "command": "python3",  
        "args": ["mcp_server.py"]
    }
}

def ensure_database_exists():
    """Guarantees the target directory and SQLite file exist before any request hits the state machine."""
    db_path = "/tmp/company.db"
    dir_path = os.path.dirname(db_path)
    
    print(f"[Database Setup] Verifying data path: {db_path}")
    
    if not os.path.exists(dir_path):
        print(f"[Database Setup] Directory {dir_path} missing. Creating it dynamically...")
        os.makedirs(dir_path, exist_ok=True)
        
    if not os.path.exists(db_path):
        print("[Database Setup] Database file missing! Building and seeding mock data...")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY,
                    customer_name TEXT,
                    status TEXT,
                    warehouse_id INTEGER,
                    item_name TEXT
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    warehouse_id INTEGER,
                    item_name TEXT,
                    stock_count INTEGER
                );
            """)
            
            cursor.execute("INSERT OR IGNORE INTO orders VALUES (4092, 'Alice Smith', 'Limbo', 1, 'Premium Shoes');")
            cursor.execute("""
                INSERT OR IGNORE INTO orders (order_id, status, warehouse_id, item_name) 
                VALUES 
                    (1001, 'Stuck', 1, 'Premium Shoes'),
                    (1002, 'Stuck', 2, 'Wireless Headphones'),
                    (1003, 'Processing', 1, 'Premium Shoes'),
                    (1004, 'Stuck', 3, 'Wireless Headphones');
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO inventory (item_name, warehouse_id, stock_count)
                VALUES 
                    ('Premium Shoes', 1, 0),
                    ('Premium Shoes', 2, 50),
                    ('Premium Shoes', 3, 10),
                    ('Wireless Headphones', 2, 0),
                    ('Wireless Headphones', 1, 35);
            """)
            conn.commit()
            conn.close()
            print(" [Database Setup] Seeding complete. Persistent schema active.")
        except Exception as db_err:
            print(f"[Database Setup] Automated fallback construction failed: {str(db_err)}")
    else:
        print("[Database Setup] Verified! Database file found intact.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n[Lifespan] Initializing system environments...")
    ensure_database_exists()

    print("[Lifespan] Booting MultiServerMCPClient...")
    
    try:
        client = MultiServerMCPClient(MCP_CONFIG)
        
        # 2. Fetch tools directly using the new API
        tools = await client.get_tools()
        mcp_context["tools"] = tools
        
        print(f"⚡ [Lifespan] Successfully bound {len(tools)} remote MCP tools dynamically.")
        

        yield


        
    except Exception as e:
        print(f"❌ [Lifespan Error] MCP Initialization failed: {str(e)}")
        mcp_context["tools"] = []
        yield


app = FastAPI(lifespan=lifespan)


slack_app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
handler = AsyncSlackRequestHandler(slack_app)


async def respond_mention_instantly(ack):
    """Acknowledge Slack immediately within 3 seconds to avoid event retries."""
    await ack()

async def process_mention_logic(event, say):
    """Heavy LangGraph execution runs safely in the background."""
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

    await say(text=f"*Consulting LangGraph State Machine for Order #{dynamic_order_id}...*", thread_ts=thread_ts)

    try:
        async for event_update in agent_brain.astream(initial_input, thread_config, stream_mode="updates"):
            if "action_execute" in event_update:
                await say(text="*Operation completed successfully on the database layer.*", thread_ts=thread_ts)

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
        await say(text=f"*System Error:* `{str(err)}`", thread_ts=thread_ts)


slack_app.event("app_mention")(ack=respond_mention_instantly, lazy=[process_mention_logic])


async def respond_action_instantly(ack):
    """Acknowledge button interactive component clicks immediately."""
    await ack()

async def handle_slack_approval_button(body, say):
    """Catches approval click, updates native interrupt, resumes execution."""
    block_id = body["actions"][0]["block_id"]
    thread_id = block_id.split("approval_block_")[-1]
    thread_config = {"configurable": {"thread_id": thread_id}}
    
    await say(text="*Approval received! Resuming LangGraph execution context...*", thread_ts=thread_id)
    
    async for event_update in agent_brain.astream(Command(resume="approved"), thread_config, stream_mode="updates"):
        pass
    
    await say(text="*Database successfully synchronized!*", thread_ts=thread_id)

async def handle_slack_rejection_button(body, say):
    """Catches rejection click and safely alerts the graph to abort."""
    block_id = body["actions"][0]["block_id"]
    thread_id = block_id.split("approval_block_")[-1]
    thread_config = {"configurable": {"thread_id": thread_id}}
    
    await say(text="*Operation rejected by human supervisor. Aborting operation cleanly.*", thread_ts=thread_id)
    
    async for event_update in agent_brain.astream(Command(resume="rejected"), thread_config, stream_mode="updates"):
        pass


slack_app.action("approve_action")(ack=respond_action_instantly, lazy=[handle_slack_approval_button])
slack_app.action("reject_action")(ack=respond_action_instantly, lazy=[handle_slack_rejection_button])


@app.post("/slack/events")
async def slack_events_endpoint(request: Request):
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    
    try:
        if body_str.startswith("payload="):
            from urllib.parse import unquote_plus
            payload_json = json.loads(unquote_plus(body_str.split("payload=")[1]))
        else:
            payload_json = json.loads(body_str)
    except Exception:
        payload_json = {}

    if payload_json.get("type") == "url_verification":
        return PlainTextResponse(content=payload_json.get("challenge"))

    return await handler.handle(request)