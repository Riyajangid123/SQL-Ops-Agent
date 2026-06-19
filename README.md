# SQLOps Agent: Incident Remediation & Database Controller for Enterprise Operations

An ultra-fast, autonomous Slack application designed as an emergency operational rescue asset. Powered by **LangGraph**, **Groq (`llama-3.3-70b-versatile`)**, and **FastAPI**, this system securely intercepts natural language reports of stuck operational database incidents directly from an enterprise chat platform, diagnoses systemic bottlenecks, formulates precision remediation queries, and executes write mutations **only after manual, non-developer human supervisor authorization**.

---

## 🚀 The Core Innovation & Business Value

In fast-paced enterprise environments, operational deadlocks (such as stuck fulfillment rows, payment confirmation desynchronizations, or zero-inventory routing loops) require immediate technical intervention. Non-technical support leads and operations managers often wait hours for a database administrator (DBA) to write an emergency patch script.

**SQLOps Agent** completely eliminates this operational downtime. It empowers non-technical staff (like support or warehouse management teams) to safely resolve critical data anomalies via natural language text inside Slack. By leveraging a strict **Human-in-the-Loop (HITL)** architecture, the AI serves as the diagnostic engineer, while the human retains 100% control over database write operations via interactive UI click events.

---

## 🛡️ Human-In-The-Loop (HITL) Security Architecture

To prevent accidental data loss, schema corruption, or unauthorized data destruction, SQLOps Agent splits read queries and structural modifications into two completely separate execution paths managed by a conditional graph router:

1. **The Read Path (`SELECT` Queries):** When an operational lead requests simple system metrics or tracking parameters, the graph bypasses the safety blocks and streams data instantly back to the chat thread.
2. **The Write Mutation Path (`UPDATE` Queries):** When the agent formulates a corrective write script to fix a stuck record, a **State-Graph Interrupt** is triggered. The state machine securely freezes in memory and posts a dynamic UI confirmation block containing an **"Approve ✅"** and **"Reject ❌"** interaction interface directly to the user's thread. The underlying SQLite instance remains untouched until a human explicitly signs off.

---

## 🛠️ Tech Stack & Graph Architecture

* **State Orchestration Framework:** LangGraph (StateGraph, Checkpoint Memory Preservation)
* **AI Inference Core:** Groq Cloud SDK (`llama-3.3-70b-versatile`) — Selected for high structural reasoning accuracy under sub-second processing budgets.
* **Backend Runtime & Webhooks Engine:** Python, FastAPI, Uvicorn, Slack Bolt Asynchronous SDK
* **Database Target Infrastructure:** SQLite (`company.db`) utilizing state-persisted checkpoints via an `InMemorySaver`.
* **Networking Secure Tunnel:** ngrok (for routing interactive webhook payloads safely to a local development environment).

### 📊 System State Machine Workflow

```text
               ┌───> [ Is SELECT Query? ] ──────> Natively run Tool ───> [ END ]
               │
[ START ] ──> [ Node 1: Diagnosis Agent ]
               │
               └───> [ Is Mutation Query? ] ───> [ Node 2: State Graph Interrupt ]
                                                             │
                                                             ▼
                                                [ Generates Slack Buttons ]
                                                             │
                                      ┌──────────────────────┴──────────────────────┐
                                      ▼                                             ▼
                             [ Human Hits Approve ✅ ]                    [ Human Hits Reject ❌ ]
                                      │                                             │
                                      ▼                                             ▼
                        [ Node 3: Action Execution ]                   [ Abort Operation Cleanly ]


D:\SQL Ops Agent\
│
├── main.py                    # FastAPI app router, entrypoint events, and interactive block listeners
├── graph/
│   ├── __init__.py
│   ├── workflow.py            # LangGraph StateGraph builder, routing logic, and checkpoint configuration
│   └── state.py               # Shared type structures defining state variables across nodes
│
├── sql_agent/
│   ├── __init__.py
│   ├── diagnosis.py           # Node 1: Multi-table anomaly detection and fix query generation
│   ├── human_approval.py      # Node 2: High-security HITL state freeze and data serialization
│   └── action_execution.py    # Node 3: Database transaction manager for human-approved scripts
│
├── database/
│   ├── __init__.py
│   └── queries.py             # Instantiates the underlying testing tables and relational parameters
│
├── company.db                 # Local transactional SQLite database infrastructure
├── .gitignore                 # Enforces security isolation boundaries around platform secrets
└── README.md                  # System architecture, capabilities overview, and pipeline maps