# Nova Multimodal Product Recommender

> **TFM (Master's Thesis) project** — An end-to-end multimodal product recommendation system combining AWS cloud AI services with a locally hosted vision-language model to deliver semantically rich, explainable product suggestions.

> 🙏 **Project Attribution:** Este proyecto fue desarrollado conjuntamente con [**Cod-ing-Koala**](https://github.com/Cod-ing-Koala) durante el TFM de Máster en Ingeniería y Desarrollo de Soluciones de IA Generativa. Este repositorio es una copia mantenida en mi perfil como parte de mi portfolio. Para el repositorio original y toda la información de desarrollo, consulta [Cod-ing-Koala/llama_vision_product_recommender](https://github.com/Cod-ing-Koala/llama_vision_product_recommender).

---

## Table of Contents

1. [Quick Start — New User Setup](#1-quick-start--new-user-setup)
2. [What's in the `.env` File](#2-whats-in-the-env-file)
3. [Project Structure](#3-project-structure)
4. [Key Capabilities](#key-capabilities)
5. [Attribution & Credits](#attribution--credits)

---

## 1. Quick Start — New User Setup

This section assumes you have received the project's `.env` file (with AWS credentials and API keys) from the project author. You do **not** need to configure any AWS account or API keys yourself.

### Prerequisites

| Requirement | Purpose |
|---|---|
| **Python 3.11+** | Runtime for the FastAPI application |
| **Docker + Docker Compose** | Recommended: runs the entire stack in containers |
| **Ollama** | Required only for local (non-Docker) setup |
| **Git** | Cloning the repository |

### Option A — Docker Compose (Recommended)

Docker Compose is the easiest way to run the full project. It handles Ollama, the FastAPI backend, and the Streamlit UI automatically.

```bash
# 1. Clone the repository
git clone https://github.com/sergiocasas14/llama_vision_product_recommender.git
cd llama_vision_product_recommender

# 2. Place the .env file you received in the project root
# (it should be at the same level as docker-compose.yml)

# 3. Start all services  — first run downloads llama3.2-vision (~4 GB)
docker compose up --build
```

Services start automatically:

| Service | URL | Description |
|---|---|---|
| Streamlit UI | http://localhost:8501 | Web interface for searching products |
| FastAPI backend | http://localhost:8000 | REST API |
| FastAPI docs | http://localhost:8000/docs | Interactive Swagger UI |
| Ollama API | http://localhost:11434 | Local LLM (managed internally) |

The vector index and product embeddings are already stored in AWS S3Vectors from the production indexing run (122,274 products). **You do not need to re-index anything**. The system is ready to use.

#### Optional: Enable NVIDIA GPU for Ollama

Uncomment the `deploy` block in `docker-compose.yml` to give Ollama access to a GPU, which significantly speeds up LLM inference.

### Option B — Local Setup (without Docker)

```bash
# 1. Clone the repository
git clone https://github.com/sergiocasas14/llama_vision_product_recommender.git
cd llama_vision_product_recommender

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
.\.venv\Scripts\Activate.ps1       # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Place the .env file you received in the project root
# (it should be at the same level as app/)

# 5. Start Ollama (model is ~4 GB, downloads on first run)
ollama pull llama3.2-vision
ollama serve                        # Starts Ollama API on port 11434

# 6. In a separate terminal, start the FastAPI backend
uvicorn app.main:app --reload       # http://localhost:8000

# 7. In a separate terminal, start the Streamlit UI
streamlit run streamlit_app.py      # http://localhost:8501
```

---

## 2. What's in the `.env` File

The `.env` file you receive contains all credentials and configuration needed to reproduce the project. Copy it to the project root (same directory as `app/` and `docker-compose.yml`).

```bash
# ─── AWS Configuration ────────────────────────────────────────────────────
# Region for Bedrock (Nova embeddings) and S3Vectors.
# IMPORTANT: nova-2-multimodal-embeddings-v1:0 is ONLY available in us-east-1.
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<provided>
AWS_SECRET_ACCESS_KEY=<provided>

# ─── Bedrock Embedding Model ──────────────────────────────────────────────
NOVA_MODEL_ID=amazon.nova-2-multimodal-embeddings-v1:0
EMBED_DIM=3072

# ─── S3Vectors (Vector Store) ────────────────────────────────────────────
VECTOR_BUCKET=nova-product-vectors-v2
VECTOR_INDEX=products-mm-v2

# ─── S3 (Data Bucket) ─────────────────────────────────────────────────────
DATA_BUCKET=nova-product-dataset-v2
DATA_BUCKET_REGION=us-east-1

# ─── Ollama (Local LLM) ───────────────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2-vision

# ─── Admin API Endpoint ───────────────────────────────────────────────────
ADMIN_TOKEN=<provided>

# ─── Streamlit UI ─────────────────────────────────────────────────────────
API_URL=http://localhost:8000
```

> **Note on `OLLAMA_BASE_URL`:** When running with Docker Compose, this is automatically overridden to `http://ollama:11434` by the Docker Compose environment section. If running locally, keep it as `http://localhost:11434`.

---

## 3. Project Structure

```
llama_vision_product_recommender/
│
├── streamlit_app.py             # Streamlit web UI
├── app/                         # FastAPI application (backend)
│   ├── main.py                  # App entrypoint & endpoints
│   ├── config.py                # Pydantic Settings
│   ├── security.py              # Admin token auth
│   ├── berkeley_dataset.py      # Product data loading
│   ├── nova_client.py           # AWS Bedrock Nova embeddings
│   ├── ollama_client.py         # Ollama LLM client
│   ├── s3vectors_client.py      # Vector store client
│   ├── indexer.py               # Indexing pipeline
│   ├── recommender.py           # Recommendation pipeline
│   └── langfuse_client.py       # Observability tracing
│
├── evaluation/                  # Evaluation framework
├── lambda/                      # AWS Lambda serverless pipeline
├── scripts/                     # Utility scripts
├── data/                        # Data files
├── docs/                        # Documentation
│
├── docker-compose.yml           # Full stack orchestration
├── Dockerfile                   # Container image
├── requirements.txt             # Python dependencies
└── .gitignore                   # Git ignore rules
```

---

## Key Capabilities

- **Multimodal search** — text-only, image-only, or combined text + image queries.
- **Semantic enrichment** — products indexed with rich natural-language paragraphs for better retrieval quality.
- **LLM-driven query planning** — Ollama automatically extracts filters from user prompts.
- **Explainable re-ranking** — human-readable reasons citing specific product attributes.
- **Interactive web UI** — Streamlit frontend with image preview and metadata.
- **Admin tooling** — token-protected endpoints for index management and bulk-indexing.

---

## Attribution & Credits

**Developers:**
- [**Cod-ing-Koala**](https://github.com/Cod-ing-Koala) — Original architect and lead developer
- **sergiocasas14** — Portfolio fork and maintenance

**Project Repositories:**
- 📌 **Original:** [Cod-ing-Koala/llama_vision_product_recommender](https://github.com/Cod-ing-Koala/llama_vision_product_recommender)
- 📋 **Portfolio Fork:** [sergiocasas14/llama_vision_product_recommender](https://github.com/sergiocasas14/llama_vision_product_recommender)

---

**Este repositorio es una copia pública del proyecto TFM desarrollado conjuntamente, mantenida como parte del portfolio profesional del desarrollador. Todo el crédito y reconocimiento del diseño original e implementación pertenece a Cod-ing-Koala.**

**For detailed documentation on architecture, AWS services, pipelines, and complete configuration, please see the original repository.**
