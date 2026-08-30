# LLM Hallucination Detection Engine

**Introduction**

This repository implements a full‑stack system for detecting factual hallucinations in large language model (LLM) responses. The backend, built with FastAPI, runs a multi‑stage verification pipeline that limits LLM API usage to two calls per answer while leveraging local embedding, NLI, and graph‑propagation models. A React + Vite frontend (named *Halluguard*) provides an interactive UI for sending prompts, visualising claim‑level analysis, and exploring the verification graph.

**Features**

- Fixed‑cost LLM verification (2 calls per answer, optional bounded escalation)
- Claim‑level confidence scores with evidence links
- Graph‑based consistency checking between claims
- FastAPI API exposing a `/pipeline` endpoint
- Production‑ready React UI with dark futuristic theme
- Development mock API (no keys required) and real‑API mode via `.env`

**Architecture**

- **Backend (Python)**: FastAPI server, modules for decomposition, retrieval, verification, aggregation, graph propagation, and escalation. Metrics and a simple HTML dashboard are included.
- **Frontend (React/TS)**: Vite‑powered UI that calls `/api/chat` (proxied to the backend) and displays real‑time analysis panels.
- **Data**: Sample dataset under `data/raw` and processing scripts to generate atomic claims.

**Getting Started**

**Prerequisites**

- Python 3.11+ and `venv`
- Node.js 20+ and npm
- A Google Gemini API key (optional; set `GOOGLE_API_KEY` in `.env` for real LLM calls)

**Backend Setup**

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate   # on Windows
   ```
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy the example environment file and add your API key if you want to use the real Gemini model:
   ```
   cp .env.example .env   # or edit the existing .env file
   ```
4. Run the server (this also processes the sample dataset):
   ```
   python main.py
   ```
   The API will be available at `http://localhost:8000`.

**Frontend Setup**

1. Change to the frontend directory:
   ```
   cd frontend
   ```
2. Install Node dependencies:
   ```
   npm install
   ```
3. Development mode (hot‑reloading):
   ```
   npm run dev
   ```
   Open `http://localhost:5173` in a browser. API calls are proxied to the backend running on port 8000.

4. Build for production:
   ```
   npm run build   # outputs to ./dist
   npm run preview # serves the built app locally
   ```

**Running the Full System**

1. Start the backend (`python main.py`).
2. In a separate terminal, start the frontend (`cd frontend && npm run dev`).
3. Navigate to `http://localhost:5173` and interact with the Halluguard UI.

**Testing**

Run the Python test suite to verify core pipeline functionality:
```bash
pytest tests
```

**Project Structure**

- `modules/` – backend pipeline components
- `frontend/` – React UI source code
- `data/` – raw and processed datasets
- `tests/` – pytest suite

**License**

This project is provided under the MIT License.
