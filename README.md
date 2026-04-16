# 🚀 Feasibility Check — AI-Powered Startup Idea Analyser

An agentic, multi-step feasibility analysis system that researches your startup idea live on the web, gathers community sentiment from Reddit, and produces a structured JSON report — all powered by a **LangGraph stateful pipeline**, **OpenAI GPT-4o-mini**, and **crawl4ai**.

![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)
![Pipeline](https://img.shields.io/badge/Pipeline-LangGraph-blueviolet)
![LLM](https://img.shields.io/badge/LLM-GPT--4o--mini-412991)
![DB](https://img.shields.io/badge/Database-PostgreSQL%20%2F%20Neon-4169E1)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB)
![Search](https://img.shields.io/badge/Search-DDGS%20%2B%20crawl4ai-orange)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Stateful Conversations** | Persistent multi-turn chat via PostgreSQL — resume any idea analysis across sessions |
| **LangGraph Pipeline** | Modular, graph-based agent with conditional routing (clarify → research → analyse) |
| **Smart Multi-Query Search** | LLM generates 3 targeted queries (competitors, market, YC-funded) instead of one broad query |
| **Reddit Intelligence** | Dedicated Reddit search lane captures real community opinions and pain points |
| **Content Quality Filtering** | Strips nav/header boilerplate; skips login walls, CAPTCHAs, and timeout pages |
| **URL Deduplication** | All URLs from all queries are deduplicated before crawling |
| **Structured JSON Report** | 7-field feasibility report: score, idea fit, competitors, opportunity, targeting, next step, reasoning chain |
| **Post-Report RAG Q&A** | Chat interactively with your generated report and scraped web data using local Qdrant vectors and MiniLM embeddings |
| **Premium Glassmorphic UI** | Dark-mode React app with a 4-step conversational state machine |

---

## 🧠 Agent Pipeline Flow

```
POST /api/chat
     │
     ▼
load_context_node          → reads full chat history from PostgreSQL
     │
     ▼ (router)
 new chat?
  ├── YES → cross_question_node    → asks 1 critical clarifying question → END
  └── NO  → modify_query_node      → LLM generates 3 targeted JSON queries
                 │
                 ▼
         web_research_node
           ├── Query 1: "{idea} startup competitors"      → filter_urls (max 6, no reddit/quora/zhihu)
           ├── Query 2: "{idea} existing products market" → filter_urls (max 6)
           ├── Query 3: "{idea} Y Combinator funded"      → filter_urls (max 6)
           └── Reddit:  "{q1} site:reddit.com"            → unfiltered (max 10)
                 │
           crawler_service (per URL):
             ├── extract_core()       → keeps first 30 meaningful lines, cap 1500 chars
             └── is_useful_content()  → skips login walls, timeouts, CAPTCHAs
                 │
                 ▼
         llm_agent_node     → feasibility prompt (general + Reddit context-aware)
                 │
                 ▼
         PostgreSQL upsert  (ChatSession + AgentStateModel + FeasibilityReport)
                 │
                 ├── (Background Thread) → text chunks → MiniLM-L6-v2 → Qdrant Vector Store
                 │
                 ▼
         → frontend renders structured report
         
Step 3 (Optional) — POST /api/qa
         User asks follow-up -> retriever queries Qdrant -> RAG QA Prompt -> Answer
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | OpenAI GPT-4o-mini |
| **Agent Orchestration** | LangGraph (StateGraph) |
| **Web Search** | DDGS (`ddgs` package) |
| **Web Crawler** | crawl4ai (async, headless) |
| **Vector Database** | Qdrant (local disk collection) |
| **Embeddings** | SentenceTransformers (`all-MiniLM-L6-v2`) |
| **Backend API** | FastAPI + Uvicorn |
| **Database** | PostgreSQL via Neon (SQLAlchemy ORM) |
| **Frontend** | React + Vite |
| **Styling** | Vanilla CSS — Glassmorphic dark-mode design |

---

## 📂 Project Structure

```
fesebility_check/
├── backend/
│   ├── api/
│   │   ├── routes.py          # POST /chat — main entry point
│   │   └── dependencies.py    # DB session injection
│   ├── core/
│   │   ├── config.py          # Pydantic settings (env vars)
│   │   ├── database.py        # SQLAlchemy engine + session
│   │   └── llm_factory.py     # GPT-4o-mini factory
│   ├── models/
│   │   └── conversation.py    # ChatSession, AgentStateModel, FeasibilityReport
│   ├── pipeline/
│   │   ├── graph.py           # LangGraph StateGraph definition
│   │   ├── state.py           # AgentState TypedDict
│   │   ├── tools.py           # All node functions
│   │   └── prompts/
│   │       ├── cross_question.py
│   │       ├── qa.py              # Follow-up RAG prompt
│   │       └── feasibility.py
│   ├── rag/
│   │   ├── embedder.py        # SentenceTransformers chunking & Qdrant upsert
│   │   └── retriever.py       # Context search logic
│   ├── scraper/
│   │   └── web.py             # ddgs_url_scrapper, extract_core,
│   │                          # filter_urls, is_useful_content, crawler_service
│   ├── app.py                 # FastAPI app + CORS + router mount
│   ├── main.py                # Uvicorn entrypoint + DB init lifespan
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx            # 3-step state machine (initial → cross_question → report)
        ├── index.css          # Design system (glassmorphic dark mode)
        └── main.jsx
```

---

## 🗄️ Database Schema

| Table | Purpose |
|---|---|
| `chat_sessions` | Every human/AI turn with idea, problem, customer context |
| `agent_states` | Persists `optimized_query`, `search_results`, `analysis` per conversation |
| `feasibility_reports` | Structured JSON fields: score, idea_fit, competitors, opportunity, targeting, next_step, chain_of_thought |

---

## 🚦 Getting Started

### 1. Clone & Configure

```bash
git clone <repo-url>
cd fesebility_check
```

Create `backend/.env`:

```env
OPENAI_API_KEY=your_openai_key_here
POSTGRES_URL=postgresql://user:password@host/dbname?sslmode=require
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend runs at → **http://localhost:8000**

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at → **http://localhost:5173** (proxies `/api` to backend)

---

## 🔁 Conversation Flow (UI)

```
Step 1 — Initial Form
  User fills: Idea Name, Name, Ideal Customer, Problem Statement
  → Agent asks ONE clarifying question

Step 2 — Cross Question
  User answers the clarifying question
  → Agent runs full web research pipeline
  → Returns structured feasibility report

Step 3 — Report Dashboard
  Displays: Score, Idea Fit, Market Opportunity,
            Competitor Landscape, Targeting, Next Step,
            Agent Reasoning Chain
```

---

## 🔍 Scraper Utilities (`scraper/web.py`)

| Function | Purpose |
|---|---|
| `ddgs_url_scrapper(query)` | Fetches up to 10 results from DuckDuckGo (region: `in-en`) |
| `filter_urls(urls, max=6)` | Removes `reddit.com`, `quora.com`, `zhihu.com`; caps list |
| `extract_core(markdown)` | Keeps first 30 lines > 40 chars; hard cap 1500 chars |
| `is_useful_content(text)` | Rejects pages with login walls, CAPTCHAs, timeouts |
| `crawler_service(urls)` | Async crawl of all URLs; applies `extract_core` + quality check |

---

## 📝 License

MIT