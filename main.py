import os
import sqlite3
import json
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
slack_app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
handler = AsyncSlackRequestHandler(slack_app)


groq_client = ChatGroq(
    model="llama-3.3-70b-versatile", 
    api_key=os.environ.get("GROQ_API_KEY")
)


def run_database_query(sql_query: str):
    """Connects to company.db, runs the SQL, and returns rows as simple text."""
    try:
        connection = sqlite3.connect("company.db")
        cursor = connection.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        
       
        columns = [desc[0] for desc in cursor.description]
        connection.close()
        
        if not rows:
            return "No records found matching that query."
            

        formatted_results = []
        for row in rows:
            row_text = ""
            for col, val in zip(columns, row):
                row_text += f"{col}: {val} | "
            formatted_results.append(row_text)
            
        return "\n".join(formatted_results)
        
    except Exception as error:
        return f"Database Error: {str(error)}"



@slack_app.event("app_mention")
async def handle_dynamic_mentions(event, say):
    user_text = event.get("text")
    thread_timestamp = event.get("ts")
    
    
    user_question = user_text.split(">")[-1].strip()
    

    await say(text="Checking the database for you... 🔍", thread_ts=thread_timestamp)
    

    system_prompt = (
        "You are an assistant that converts natural language into raw SQL queries. "
        "The database is SQLite and contains a file named 'company.db'. "
        "You must return ONLY the raw SQL string inside a JSON object format like this: "
        '{"sql": "SELECT * FROM orders;"}. Do not include markdown blocks or extra text.'
    )
    
    try:
       
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert this request to SQL: {user_question}"}
            ]

            completion = groq_client.invoke(messages)

            groq_response = completion.content.strip()

            parsed_json = json.loads(groq_response)
            generated_sql = parsed_json.get("sql")

            db_output = run_database_query(generated_sql)

            final_reply = f"📊 *Query Executed:* `{generated_sql}`\n\n*Results:*\n{db_output}"
            await say(text=final_reply, thread_ts=thread_timestamp)
        
    except Exception as err:
        await say(text=f"Sorry, I couldn't process that request. Error: {str(err)}", thread_ts=thread_timestamp)


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