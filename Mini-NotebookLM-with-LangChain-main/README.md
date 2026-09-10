# langchain-notebooklm

A NotebookLM-style **grounded research assistant**, built as a project for learning
**LangChain v1**. The application uses an AI Agent with RAG capabilities, document
retrieval, web search, and a human-in-the-loop source selection flow.

## Stack

- **Chat model:** Anthropic Claude (`anthropic:claude-sonnet-4-6` by default)
- **Embeddings:** Cohere (`embed-multilingual-v3.0` by default)
- Everything is provider-agnostic via env vars — see [`.env.example`](.env.example).
- **Web search:** Firecrawl
- **Backend:** FastAPI
- **Frontend:** Static Web Client (HTML/JS/CSS)

## The app

A NotebookLM-style 3-panel workspace, with a real client/server split:

```
┌ Sources ────┬ Chat ───────────────┬ Studio ──────┐
│ add / upload│ grounded answers    │ artifacts    │
│ select      │ with citations      │ + saved notes│
│ view / del  │                     │              │
└─────────────┴─────────────────────┴──────────────┘
```

- **Sources** — add by pasting text or uploading `.md`/`.txt`, toggle which sources are
  active (retrieval is scoped to them), view or remove a source.
- **Chat** — the main product: a single conversational agent for grounded Q&A with
  citations and short-term memory; save any answer to a note.
- **Studio** — generate artifacts: **Infographic · PowerPoint · Summary · FAQ**
  (each will be its own standalone agent; PowerPoint uses a `.pptx` generation skill).
- **AI Agent capabilities** — the chat agent uses RAG over uploaded sources and can
  extend its knowledge with web search using Firecrawl. External sources are selected
  by the user through a Human-in-the-loop approval flow before being added.

## Structure

```
client/                 web client — single-page HTML/JS/CSS, no build step
src/notebooklm/
  agents/               one agent per feature
    chat.py             the conversational chat agent (tools + short-term memory)
  core/                 config, models, source ingestion, the live SourceStore
  api/                  FastAPI backend: schemas (contract), services, routes
```

The chat is one simple agent with the retrieval tools and memory. The Studio artifact
generators will be standalone, stateless agents (invoked directly by the Studio, not part of
the chat). Capabilities not built yet return `501` and the UI shows a "coming soon" notice.

## Quick start

```bash
uv sync
cp .env.example .env         # fill in ANTHROPIC_API_KEY, COHERE_API_KEY and FIRECRAWL_API_KEY
uv run notebooklm-serve      # then open http://127.0.0.1:8000
```

CLI (no server):

```bash
uv run notebooklm "Compare Fleet OS growth between Q1 and Q2."
```

## Feature roadmap

| Feature | Status |
|---------|--------|
| Retrieval (grounded Q&A) | ✅ done — the `chat` agent's tools |
| Agent + tools | ✅ done — `agents/chat.py` |
| Short-term memory | ✅ done — checkpointer + `thread_id` on the chat agent |
| Structured output (Studio artifacts) | ⏳ planned |
| Event streaming | ⏳ planned |
| Middlewares | ⏳ planned |
| Guardrails | ⏳ planned |
| Human in the loop | ✅ done — source selection approval flow |
| MCP | ⏳ planned |

The sample corpus under [`src/notebooklm/data`](src/notebooklm/data) is a fictional company
("Acme Robotics") so the app runs out of the box.
