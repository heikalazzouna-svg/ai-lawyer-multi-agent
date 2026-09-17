# ⚖️ AI Lawyer: Enterprise Multi-Agent RAG System

![AI Lawyer Banner](https://img.shields.io/badge/AI%20Lawyer-Multi--Agent%20RAG-6366f1?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic%20Orchestration-2e7d32?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-f55036?style=flat-square)
![Presidio](https://img.shields.io/badge/Microsoft%20Presidio-PII%20Protection-0078d4?style=flat-square)

An Enterprise-grade LegalTech platform leveraging a state-of-the-art **Multi-Agent RAG (Retrieval-Augmented Generation)** architecture orchestrated with **LangGraph**. Designed to autonomously analyze, audit, summarize, and compare complex contracts and legal documents in real time with page-level citation verification.

---

## 📸 App Previews

<!-- Place your screenshots in a folder (e.g., /screenshots or /assets) and link them below -->
<img width="880" height="900" alt="image" src="https://github.com/user-attachments/assets/42639d7c-4a94-4bc5-b74a-666ca960b1e2" />
<img width="945" height="435" alt="image" src="https://github.com/user-attachments/assets/c444f789-953d-4271-9587-041d31417a69" />
<img width="945" height="445" alt="image" src="https://github.com/user-attachments/assets/bb767c25-ed8a-4d7c-a555-d66994f8536e" />
<img width="945" height="515" alt="image" src="https://github.com/user-attachments/assets/645c42cd-5063-4ba7-8a00-5b69ef9fe71e" />
<img width="945" height="541" alt="image" src="https://github.com/user-attachments/assets/3c017f47-070c-4819-bc26-8b7a2cb778e6" />
<img width="945" height="469" alt="image" src="https://github.com/user-attachments/assets/82c16d2c-7829-4f1e-af67-bf7b335ecaae" />










---

## ✨ Key Features

### 1. 🧠 Multi-Agent Architecture (LangGraph)
Unlike single-prompt LLM wrappers, AI Lawyer routes every request through an autonomous graph of specialized agents:
* **Supervisor Agent:** Analyzes user intent and dynamically routes the task to the right specialist.
* **Legal Researcher:** Performs deep semantic search over document chunks and retrieves answers strictly from source text. Equipped with **DuckDuckGo Web Search** for external case law when needed.
* **Risk Assessor:** Audits documents across 7 critical legal checkpoints (Liability, Termination, Non-Compete, IP, Governing Law, Data Privacy, and Missing Clauses) with severity ratings (🔴 High, 🟡 Medium, 🟢 Low).
* **Contract Comparator:** Performs cross-document analysis when multiple PDFs are uploaded, pinpointing changes, conflicting terms, and clause variances.
* **Legal Drafter:** Compiles professional memos, client summaries, and executive briefings.
* **Citator Quality Gate:** An automated quality check verifying every factual claim against context metadata, tagging any potential hallucination with `[UNVERIFIED]` or `[CITATION ERROR]`.

### 2. ⚡ Real-Time Streaming (SSE)
* End-to-end token streaming powered by **Server-Sent Events (SSE)**.
* Live agent status chips (*Classifying intent...*, *Analyzing documents...*, *Verifying citations...*) delivering a transparent, ChatGPT-like experience.

### 3. 🛡️ Enterprise Security & Privacy
* **Microsoft Presidio Integration:** Automatically detects and anonymizes personally identifiable information (PII: names, emails, phones, SSNs) prior to LLM processing.
* **Full Authentication Flow:** Bcrypt password hashing, JWT session management, and real SMTP email verification links.
* **Persistent Sessions:** Multi-session history backed by SQLite and SQLAlchemy.

### 4. 📚 Advanced RAG Engine
* **Vector Store:** FAISS index combined with HuggingFace embeddings for sub-second chunk retrieval.
* **Page-Level Grounding:** Extracts page metadata to provide verifiable citations (e.g., `[Contract.pdf, Page 4]`).
* **Initial Counsel Scan:** Automatically extracts governing law, liabilities, and termination conditions immediately upon upload.

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Next.js 14, TailwindCSS, TypeScript, Lucide Icons, PDF Viewer |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, SQLite, Pydantic |
| **AI & Orchestration** | LangGraph, LangChain, FAISS Vector Store, HuggingFace Embeddings |
| **LLM Inference** | Groq API (High-throughput LPU inference with DeepSeek / Llama / OSS models) |
| **Security & Privacy** | Microsoft Presidio, Passlib (Bcrypt), Python-JOSE (JWT), SMTP |

---

## 🚀 Quick Start

### Prerequisites
* **Python 3.10+**
* **Node.js 18+** & **npm**
* A free **Groq API Key** (from [console.groq.com](https://console.groq.com))

---

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/heikalazzouna-svg/ai-lawyer-multi-agent.git
cd ai-lawyer-multi-agent

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate      # On Windows
# source venv/bin/activate   # On Linux/macOS

# Install backend dependencies
pip install -r requirements.txt

# Configure environment variables (.env)
# Create a .env file in the root directory:
GROQ_API_KEY="your_groq_api_key_here"
GROQ_MODEL_NAME="openai/gpt-oss-120b"
SMTP_EMAIL="your.email@gmail.com"
SMTP_PASSWORD="your_gmail_app_password"

# Launch the FastAPI server
python api_server.py
```
> The API backend will be live at `http://localhost:8000` (API Docs: `http://localhost:8000/docs`).

---

### 2. Frontend Setup

```bash
# Open a new terminal and navigate to the web directory
cd web

# Install frontend dependencies
npm install

# Run the development server
npm run dev
```
> The web application will be accessible at **`http://localhost:3000`**.

---

## 📁 Repository Structure

```
├── agents/                  # LangGraph multi-agent orchestration
│   ├── graph.py             # Compiled StateGraph definition
│   ├── stream_graph.py      # Real-time SSE streaming graph pipeline
│   ├── nodes.py             # Agent node logic (Researcher, Assessor, Comparator, Citator)
│   └── prompts.py           # Domain-tuned legal agent prompts
├── api_server.py            # FastAPI application routes & SSE endpoints
├── rag_pipeline.py          # Document parsing, chunking & RAG retrieval
├── vector_database.py       # FAISS vector store initialization & indexing
├── security.py              # Microsoft Presidio PII anonymization module
├── auth.py                  # JWT authentication & password hashing
├── models.py                # Database models (Users, Chat History)
├── database.py              # SQLAlchemy engine configuration
├── web/                     # Next.js frontend application
│   ├── src/app/page.tsx     # Single-page application UI with split PDF viewer
│   └── ...
└── README.md                # Project documentation
```

---

## ⚖️ Disclaimer
*This project is an AI-powered legal assistant intended for research, document review, and demonstration purposes. It does not constitute formal legal advice.*
