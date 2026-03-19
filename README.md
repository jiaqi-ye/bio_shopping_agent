# BioShopping Agent (Research Animals Procurement Assistant)

Full-stack demo for laboratory animal procurement with a FastAPI + SQLite backend, a React + Vite frontend, and optional OpenAI + RAG support.

**Features (Complete List)**
- FastAPI backend with CORS enabled and OpenAPI docs at `/docs`.
- `/api/chat` assistant endpoint with conversation memory and mode switching (`chat`, `procurement`, `knowledge`).
- Irrelevant-request filter for non-procurement topics.
- New-user onboarding with required profile fields (username, password, shipping address, current mouse count, cage capacity).
- `/api/login` to create/update user profiles and `/api/profile/{user_id}` to fetch them.
- Per-user order limit check based on current mouse count and cage capacity.
- Common mice helper that returns the top 10 strains with descriptions.
- Order-intent detector that returns quick vendor links.
- Mouse strain extraction and antibody target extraction.
- HTML response rendering with vendor/company links and optional detail tables.
- Optional OpenAI responses with system prompts specialized for mouse strain requests.
- Local fallback responses when OpenAI is not configured.
- RAG ingestion for PDFs via `/api/upload_pdf`.
- RAG search over ingested PDFs with source citations.
- Optional web scraping (allowlist + cache) to ingest vendor pages for RAG.
- Vendor CRUD: `GET /vendors`, `GET /vendors/{id}`, `POST /vendors`, `PUT /vendors/{id}`, `DELETE /vendors/{id}`.
- Strain CRUD: `GET /strains`, `GET /strains/{id}`, `POST /strains`, `PUT /strains/{id}`, `DELETE /strains/{id}`.
- Cage configuration CRUD: `GET /cages`, `GET /cages/{id}`, `POST /cages`, `PUT /cages/{id}`, `DELETE /cages/{id}`.
- Procurement endpoint `POST /procure` with compliance checks, cage capacity checks, allocation, lead time planning, latest order date, and RFQ draft.
- Procurement history endpoint `GET /history` for stored procurement records.
- SQLite seed data for vendors, strains, and cage configuration.
- CLI client (`backend/cli.py`) to run the `/procure` endpoint from the terminal.
- Deterministic fallback embeddings when OpenAI embeddings are unavailable.
- FAISS-based vector index for fast semantic search (optional if FAISS is installed).
- React UI with multi-conversation sidebar (new chat, rename, delete).
- Login modal to capture lab profile and persist user ID in local storage.
- Chat window with quick action buttons and live “Thinking...” state.
- Speech-to-text input using the browser SpeechRecognition API.
- HTML message rendering with safe table extraction.
- One-click “View as Table” for HTML tables and comparison payloads.
- Full-screen table view and CSV download for large tables.
- Source list rendering with optional clickable URLs.
- Additional UI modules included in the codebase: analytics charts, agent reasoning pipeline cards, procurement planner inputs, RFQ lead-time card, and vendor cards.
- Docker support for backend + frontend via `docker-compose.yml` and Dockerfiles.
- Test suite for intent classification and procurement APIs.

## Project Layout

- `F:\BioShopping_Agent\backend\main.py`: FastAPI app and endpoints
- `F:\BioShopping_Agent\backend\db.py`: SQLite init + seed data
- `F:\BioShopping_Agent\backend\logic.py`: Procurement context, checks, and legacy `/procure`
- `F:\BioShopping_Agent\backend\agent.py`: Chat orchestration, profile flow, and response rendering
- `F:\BioShopping_Agent\backend\rag_service.py`: RAG ingestion + search
- `F:\BioShopping_Agent\backend\web_scraper.py`: Allowlisted vendor scraping
- `F:\BioShopping_Agent\backend\llm_client.py`: OpenAI response and prompt logic
- `F:\BioShopping_Agent\backend\embeddings.py`: OpenAI embeddings + fallback
- `F:\BioShopping_Agent\frontend\src\App.tsx`: Main React app
- `F:\BioShopping_Agent\frontend\src\components\*`: UI components for chat and layout
- `F:\BioShopping_Agent\tests\*`: Pytest coverage
- `F:\BioShopping_Agent\docker\*`: Dockerfiles

## Quickstart (Local)

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r backend/requirements.txt

uvicorn backend.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## Run the React Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` and set `VITE_API_BASE` to your FastAPI server if needed.

## CLI Demo

Start the API first, then:

```bash
python backend/cli.py
```

## Example Procure Request

```bash
curl -X POST http://127.0.0.1:8000/procure \
  -H "Content-Type: application/json" \
  -d '{"strain":"C57BL/6J","quantity":60,"experiment_start_date":"2026-03-20","approved_quota":50}'
```

## RAG: Upload a PDF

```bash
curl -X POST http://127.0.0.1:8000/api/upload_pdf \
  -F "file=@./path/to/protocol.pdf"
```

## Docker

```bash
docker compose up --build
```

Backend: `http://127.0.0.1:8000`  
Frontend: `http://127.0.0.1:3000`

## Configuration (.env)

- `OPENAI_API_KEY`: Enable OpenAI chat + embeddings
- `CHAT_MODEL`: Chat model for assistant responses
- `EMBEDDING_MODEL`: Embedding model name
- `EMBEDDING_DIM`: Fallback embedding dimension
- `DATABASE_PATH`: SQLite database path
- `VECTOR_INDEX_PATH`: FAISS index path
- `VECTOR_META_PATH`: Vector metadata path
- `VITE_API_BASE`: Frontend API base URL
- `CORS_ORIGINS`: CORS allowlist
- `ENABLE_WEB_SCRAPE`: Enable allowlisted vendor scraping
- `WEB_ALLOWLIST_DOMAINS`: Allowed domains for scraping
- `VENDOR_SOURCE_URLS`: Comma-separated vendor URLs to ingest
- `BACKEND_PORT`, `FRONTEND_PORT`: Docker compose ports

## Run Tests

```bash
pytest -q
```

## Notes

- Seeded vendors include The Jackson Laboratory, Charles River, and Taconic Biosciences.
- Seeded strains include C57BL/6J, BALB/c, DBA/2, FVB/N, 129S1/SvImJ.
- `available_strains` is stored as JSON in SQLite and encodes per-vendor strain capacity for demo allocation.
