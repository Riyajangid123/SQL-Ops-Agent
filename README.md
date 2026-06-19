# SQLOps Agent: Natural Language Database Controller for Enterprise Teams

An ultra-fast, dynamic Slack application that bridges the gap between non-technical team members and relational databases. Powered by **LangChain**, **Groq (`llama-3.3-70b-versatile`)**, and **FastAPI**, this agent securely intercepts natural language instructions straight from an enterprise chat platform, translates them into optimized raw SQL syntax, executes live operations on a local database engine, and prints beautifully formatted real-time outputs back to the chat interface.

---

## 🚀 The Core Innovation

In fast-paced corporate environments, non-technical managers, operational leads, and support agents face massive friction when seeking real-time database insights—often waiting hours for dedicated data analysts to write simple lookup queries. 

**SQLOps Agent** eliminates this bottleneck entirely. By transforming standard collaboration channels into structured data pipelines, anyone on the team can safely text-query complex business infrastructure and get millisecond answers without knowing a single line of database code.

---

## 🛠️ Tech Stack & Architecture

* **Backend Engine:** Python, FastAPI, Uvicorn
* **Orchestration Framework:** LangChain (Structured LLM Parsing Interface)
* **AI Inference Core:** Groq Cloud SDK (`llama-3.3-70b-versatile`) — Selected for near-instant latency and high structural reasoning accuracy.
* **Collaboration Layer:** Slack Bolt SDK for Python & Slack Webhooks API
* **Database Pipeline:** SQLite (`company.db`) utilizing parameterized transactions and column-index filtering.
* **Networking Secure Tunnel:** ngrok (for routing interactive webhook payloads safely to a local runtime environment).

### 📊 System Workflow
`Slack Workspace UI` ➡️ `Secure ngrok Tunnel` ➡️ `FastAPI Event Routing Router` ➡️ `LangChain / Groq LLM Translation` ➡️ `Local SQLite DB Execution` ➡️ `Formatted Real-Time Markdown Output Back to Slack Thread`

---

## ✨ Features Built & Verified

* **Natural-Language-to-SQL Processing:** Intelligently maps variable conversational statements into structured SQL scripts (e.g., handles conditional filtering, data lookups, and aggregate functions automatically).
* **Enterprise Channel Integrations:** Triggers asynchronously via standard event-driven `@app_mention` listeners inside secure team channels.
* **Asynchronous Execution Architecture:** Built on top of Python's async stack (`AsyncApp`, `aiohttp`, `FastAPI`), preventing application deadlocks during multi-user workloads.
* **Fault-Tolerant Parsing Loops:** Features strict backend data validation handling to parse model JSON payloads cleanly, printing clear error reports back to threads if an unstable prompt is evaluated.

---

## 📂 Project Directory Structure

```text
D:\SQL Ops Agent\
│
├── main.py                # Core FastAPI app router, Slack listeners, and data pipelines
├── company.db             # Local SQLite database holding business & customer records
├── .gitignore             # Strict token and cache isolation guardrails
└── README.md              # Technical project documentation & architectural breakdown