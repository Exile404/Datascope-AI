# DataScope AI

> Intelligent data analysis platform powered by a custom fine-tuned LLM. Upload any CSV, get production-grade exploratory data analysis, statistical insights, and ML recommendations from a model trained from the ground up.

![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Next.js](https://img.shields.io/badge/Next.js-15-black)

---

## Overview

DataScope AI is a full-stack ML system built end-to-end without relying on hosted LLM APIs. The core is a **fine-tuned Llama 3.1 8B** model trained on 10,000 synthetic dataset profiles spanning 14 domains, served via a FastAPI backend with LangChain orchestration, and consumed by a Next.js dashboard.

The model takes a statistical profile of any CSV (computed by the backend) and generates structured analysis covering distributions, correlations, data quality, and actionable ML recommendations.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  Next.js 15     │────▶│  FastAPI         │────▶│  Fine-Tuned LLM       │
│  + shadcn/ui    │◀────│  + LangChain     │◀────│  (Llama 3.1 8B + LoRA)│
│  + TanStack     │ JSON│  + Pandas/SciPy  │     │  served via Ollama    │
└─────────────────┘     └──────────────────┘     └──────────────────────┘
     Frontend                Backend                   ML Pipeline
```

**Three pillars, clean separation:**

- **Frontend** — UI dashboard, no business logic
- **Backend** — CSV parsing, statistical profiling, LLM orchestration
- **ML** — training pipeline, fine-tuned model

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Base Model | Llama 3.1 8B Instruct (4-bit quantized) |
| Fine-Tuning | Unsloth + LoRA (r=16, alpha=32) |
| Inference | Ollama (GGUF Q4_K_M) |
| Backend | FastAPI, Pydantic, LangChain, Pandas, SciPy |
| Frontend | Next.js 15, TypeScript, Tailwind CSS v4, shadcn/ui |
| State | TanStack Query |
| UI Library | shadcn/ui (Radix primitives) |
| Icons | Lucide |
| Markdown | react-markdown + remark-gfm |

## Features

### Data Profiler ✅
Upload any CSV and receive:
- Automated statistical profiling (mean, std, skewness, kurtosis, IQR, outliers)
- Correlation analysis with strength classification
- Data quality scoring with column-level callouts
- AI-generated insights with actionable ML recommendations
- Reasoning trace (chain-of-thought visibility)

### Coming Soon
- **LLM Evaluator** — multi-temperature comparison with quality scoring
- **Drift Monitor** — semantic drift, hallucination detection, performance tracking
- **Cost Analyzer** — token cost projections across models

## Project Structure

```
datascope-ai/
├── ml/                          # ML pipeline
│   ├── configs/
│   │   ├── model_config.yaml    # Base model + LoRA settings
│   │   └── training_config.yaml # Hyperparameters
│   ├── scripts/
│   │   ├── generate_training_data.py  # Synthetic data generator
│   │   ├── train.py             # Unsloth fine-tuning
│   │   └── export.py            # Model export
│   └── data/processed/
│       └── datascope_train.toon # 10K training examples
│
├── backend/                     # FastAPI server
│   ├── app/
│   │   ├── api/                 # Route handlers
│   │   ├── core/                # LLM engine
│   │   ├── models/              # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── config.py
│   │   └── main.py
│   └── requirements.txt
│
└── frontend/                    # Next.js dashboard
    ├── src/
    │   ├── app/                 # Pages (App Router)
    │   ├── components/          # UI components
    │   ├── hooks/               # TanStack Query hooks
    │   ├── lib/                 # API client, constants
    │   └── types/               # TypeScript interfaces
    └── package.json
```

## Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm 9+
- NVIDIA GPU with 16GB+ VRAM (for training)
- Ollama (for serving)

### 1. Clone the repository

```bash
git clone https://github.com/exile404/datascope-ai.git
cd datascope-ai
```

### 2. ML Pipeline (Optional — if you want to retrain)

```bash
cd ml
python3 -m venv ml-env
source ml-env/bin/activate
pip install -r requirements.txt
pip install -r requirements-train.txt

# Generate training data
python scripts/generate_training_data.py --num_examples 10000

# Train the model
cd scripts
python train.py
```

### 3. Backend

```bash
cd backend
python3 -m venv backend-env
source backend-env/bin/activate
pip install -r requirements.txt

# Copy env template
cp .env.example .env

# Run the server
uvicorn app.main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
pnpm install

# Set the backend URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

pnpm dev
```

App available at http://localhost:3000

### 5. Ollama (for serving the model)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Create the model from the trained GGUF
cd ml/scripts/models/datascope-analyst-gguf_gguf
ollama create datascope-analyst -f ./Modelfile

# Verify
ollama list
```

## Usage

1. Start Ollama (`ollama serve` or as system service)
2. Start backend (`uvicorn app.main:app --reload --port 8000`)
3. Start frontend (`pnpm dev`)
4. Open http://localhost:3000
5. Click "Try the Profiler"
6. Upload any CSV
7. Wait 30-90 seconds for analysis

## Training Details

### Dataset

- **10,000 synthetic examples** across 14 domains:
  E-Commerce, Healthcare, Finance, HR, IoT, Education, Marketing, Real Estate, Logistics, Social Media, Cybersecurity, Retail, Weather, Sports
- **Format**: Custom `.toon` format with `[system]`, `[input]`, `[output]` blocks
- **Augmentation**: Random distributions (normal, log-normal, beta, exponential, t-distribution, bimodal), realistic correlations, missing value injection

### Hyperparameters

```yaml
base_model: unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit
lora:
  r: 16
  alpha: 32
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
training:
  epochs: 3
  effective_batch_size: 16
  learning_rate: 2e-4
  scheduler: cosine
  warmup_ratio: 0.05
  precision: bf16
```

### Results

- Final training loss: **0.4815**
- Trained in ~7 hours on RTX 5060 Ti (16GB)
- Exported as merged safetensors + GGUF Q4_K_M

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (API + LLM status) |
| POST | `/api/profiler/profile` | CSV → statistics only (fast) |
| POST | `/api/profiler/insight` | CSV → full LLM analysis |
| POST | `/api/profiler/insight/stream` | Streaming version (SSE) |

## Roadmap

- [ ] Multi-agent orchestration (specialized statistician/correlation/quality/strategist agents)
- [ ] Streaming token output in UI
- [ ] LLM Evaluator tab (model comparison + quality scoring)
- [ ] Drift Monitor tab (semantic drift, hallucination detection)
- [ ] Cost Analyzer tab (token economics)
- [ ] Histogram + correlation heatmap visualizations
- [ ] Docker Compose for one-command deployment
- [ ] Vercel + Railway deployment

## Author

**Tahsinul Haque Dhrubo**
Master of Data Science — Deakin University
[GitHub: @exile404](https://github.com/exile404)

## License

MIT

## AI Usage
Used AI to create readme.md and debugging the code