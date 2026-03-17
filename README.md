# Research Animals Procurement Agent (Demo)

Complete runnable demo with FastAPI + SQLite backend and a CLI interface. The demo includes vendor matching, strain equivalence recommendations, lead time planning, order splitting, compliance checks, cage capacity checks, RFQ generation, and a procurement history data flywheel.

## Project Layout

- app/main.py: FastAPI app and endpoints
- app/db.py: SQLite init + seed data
- app/logic.py: procurement planning logic
- app/schemas.py: Pydantic models
- app/cli.py: CLI demo client
- tests/test_procure.py: basic unit tests
- procurement.db: SQLite database (created on first run)

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`

## Run the CLI Demo

Start the API first, then:

```bash
python app/cli.py
```

The default CLI inputs request 60 mice of C57BL/6J, which forces a split order across multiple vendors based on seeded capacities.

## Example Procure Request

```bash
curl -X POST http://127.0.0.1:8000/procure \
  -H "Content-Type: application/json" \
  -d '{"strain":"C57BL/6J","quantity":60,"experiment_start_date":"2026-03-20","approved_quota":50}'
```

## Run Tests

```bash
pytest -q
```

## Run the React Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` and point the API base URL to your FastAPI server.

## Notes

- Seeded vendors include The Jackson Laboratory, Charles River, and Taconic Biosciences.
- Seeded strains include C57BL/6J, BALB/c, DBA/2, FVB/N, 129S1/SvImJ.
- `available_strains` is stored as JSON in SQLite and encodes per-vendor strain capacity for demo allocation.
