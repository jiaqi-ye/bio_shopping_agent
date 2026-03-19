# BioShopping Agent

<p align="center">
  <img src="frontend/src/assets/logo.svg" alt="BioShopping Agent Logo" width="120" />
</p>

<p align="center">
  <strong>AI-Powered Laboratory Animal Procurement Assistant</strong>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/d600e520-31e9-4675-af94-c60ab47b22ca" alt="Interface Overview" width="100%" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/169317ec-f782-4878-87fc-bccdb4c7a9f6" alt="Chat Interface" width="100%" />
</p>


BioShopping Agent is a full-stack intelligent system for **laboratory animal procurement**, designed as a **multi-step reasoning agent** that integrates vendor matching, experimental planning, compliance validation, and logistics optimization.

Built with **FastAPI + SQLite (backend)** and **React + Vite (frontend)**, with optional **LLM + RAG support**.


## Overview

BioShopping Agent functions as a **decision-support system**, helping researchers:

- Select appropriate mouse strains  
- Compare vendors (price, mutation, availability)  
- Plan procurement timelines  
- Validate compliance (IACUC, quotas)  
- Optimize logistics and cage allocation  
- Generate RFQ and ordering emails  


## Reasoning Pipeline

The system follows a structured pipeline:

1. **Vendor Matching & Strain Equivalence**  
2. **Lead Time Planning & RFQ Generation**  
3. **Capacity Allocation & Logistics Optimization**  
4. **IACUC Compliance Check**  
5. **Cage Capacity Check**  
6. **Data Flywheel (Learning Loop)**  

→ Enables **constraint-aware planning + logical reasoning**


## Core Capabilities

### Vendor Matching
- Supports:
  - **Common strains** → multi-vendor comparison  
  - **Unique strains** → exclusive vendor identification  
- Provides price, mutation, availability, and alternatives  

### RFQ & Planning
- Computes order timeline  
- Generates:
  - RFQ  
  - Email draft with user info  

### Constraint Checking
- IACUC protocol validation  
- Cage capacity verification  

### Optimization
- Multi-vendor allocation  
- Logistics-aware decision making  

### Learning System
- Tracks vendor performance, price, and delivery  
- Improves future recommendations  


## Key Features

- Multi-mode assistant (`chat`, `procurement`, `knowledge`)
- Context-aware reasoning
- Automatic RFQ + email generation
- Vendor comparison & recommendation
- RAG-based knowledge retrieval
- Clean ChatGPT-style UI
- Table view + CSV export
- Docker-ready full-stack system



## Quick Start

### 1. Backend Setup

```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate
pip install -r backend/requirements.txt

uvicorn backend.main:app --reload

Backend will run at:
→ http://127.0.0.1:8000

→ API Docs: http://127.0.0.1:8000/docs

### 2. Frontend Setup
cd frontend
npm install
npm run dev

Frontend will run at:
→ http://127.0.0.1:5173

### 3. Environment Configuration (.env)

Create a .env file:

copy .env.example .env

Key variables:

OPENAI_API_KEY — enables LLM features (optional)

CHAT_MODEL — chat model name

EMBEDDING_MODEL — embedding model

DATABASE_PATH — SQLite database path

VECTOR_INDEX_PATH — vector index storage

VECTOR_META_PATH — metadata storage

CORS_ORIGINS — allowed origins

ENABLE_WEB_SCRAPE — enable vendor scraping

WEB_ALLOWLIST_DOMAINS — scraping whitelist

BACKEND_PORT / FRONTEND_PORT — ports (Docker only)

### 4. Run with Docker (Recommended)
docker compose up --build

Services:

Backend → http://127.0.0.1:8000

Frontend → http://127.0.0.1:3000

### 5. Run Tests
pytest -q
