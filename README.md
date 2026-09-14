# ⚖️ AI Lawyer: Multi-Agent RAG System

![AI Lawyer Banner](https://img.shields.io/badge/AI%20Lawyer-Multi--Agent%20RAG-indigo?style=for-the-badge) 
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square) 
![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square)
![LangGraph](https://img.shields.io/badge/LangGraph-AI-green?style=flat-square)

AI Lawyer is a cutting-edge, Enterprise-grade LegalTech platform. It leverages a **Multi-Agent RAG (Retrieval-Augmented Generation) Architecture** to autonomously analyze, summarize, and compare complex legal documents in real-time.

## ✨ Key Features

* 🤖 **Multi-Agent Architecture (LangGraph):** A specialized team of AI agents working together:
  * **Supervisor:** Routes user queries to the appropriate specialist.
  * **Legal Researcher:** Answers factual questions based purely on document context.
  * **Risk Assessor:** Identifies liabilities, missing clauses, and red flags.
  * **Contract Comparator:** Analyzes multiple uploaded contracts side-by-side to highlight differences.
  * **Citator:** A strict quality gate that verifies all LLM claims have accurate page-level citations.
* 📄 **Multi-Document Comparison:** Upload multiple PDFs and ask the AI to compare specific clauses across different versions of a contract.
* ⚡ **Real-Time Streaming:** Server-Sent Events (SSE) provide a ChatGPT-like responsive UI, streaming tokens as the AI generates them.
* 🔒 **Enterprise Security & Privacy:**
  * **PII Redaction:** Microsoft Presidio automatically masks personally identifiable information before sending it to the LLM.
  * **Secure Auth:** JWT-based sessions, bcrypt password hashing, and mandatory SMTP email verification.
* 🧠 **Advanced RAG Pipeline:** FAISS vector database with HuggingFace embeddings for high-precision, sub-second document retrieval.

## 🛠️ Technology Stack

**Frontend:** React, Next.js, TailwindCSS, Lucide Icons  
**Backend:** Python, FastAPI, SQLite (SQLAlchemy)  
**AI & Machine Learning:** LangChain, LangGraph, DeepSeek R1 / Llama 3 (via Groq API), FAISS, Microsoft Presidio

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+
* A Groq API Key

### 1. Backend Setup (FastAPI)
```bash
# Clone the repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (.env)
GROQ_API_KEY="your-api-key"
SMTP_EMAIL="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"

# Start the server
python api_server.py
```

### 2. Frontend Setup (Next.js)
```bash
# Navigate to the web directory
cd web

# Install dependencies
npm install

# Start the development server
npm run dev
```

The application will be available at `http://localhost:3000`.

## 🤝 Architecture Overview
The system does not rely on a single LLM call. Instead, documents are vectorized and indexed upon upload. User queries are evaluated by the **Supervisor**, which delegates the task to a specialized agent. The final output is verified by the **Citator** to guarantee zero hallucinations and strict page-level sourcing before being streamed back to the client.
