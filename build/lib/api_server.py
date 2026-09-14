"""
AI Lawyer API Bridge — Powered by LangGraph Multi-Agent System.

This FastAPI server connects the Next.js React frontend to the
LangGraph multi-agent pipeline. Each user query flows through:

    Supervisor → Specialist Agent → Citator → Response

Endpoints:
    POST /upload  — Upload PDFs, index them, run proactive scan
    POST /chat    — Run the full multi-agent pipeline on a query
    GET  /pdfs/*  — Serve uploaded PDFs for the React PDF viewer
"""

import os
import shutil
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from vector_database import index_pdf, retrieve_docs, PDFS_DIRECTORY
from rag_pipeline import proactive_scan
from agents.graph import create_legal_agent_graph

app = FastAPI(
    title="AI Lawyer — Multi-Agent API",
    description="LangGraph-powered legal document analysis with Supervisor routing.",
    version="2.0.0",
)

# Enable CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure PDFs directory exists
os.makedirs(PDFS_DIRECTORY, exist_ok=True)

# Mount the PDFs directory so Next.js can embed the PDFs in an iframe
app.mount("/pdfs", StaticFiles(directory=PDFS_DIRECTORY), name="pdfs")

# Compile the LangGraph once at startup
legal_graph = create_legal_agent_graph()


class ChatRequest(BaseModel):
    query: str
    filenames: List[str]


@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload PDFs, index them into the vector store, and run a proactive legal scan."""
    uploaded_names = []
    
    for file in files:
        if not file.filename.endswith('.pdf'):
            continue
            
        file_path = os.path.join(PDFS_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        index_pdf(file_path)
        uploaded_names.append(file.filename)
        
    if not uploaded_names:
        raise HTTPException(status_code=400, detail="No valid PDFs uploaded.")
        
    # Run proactive scan
    scan_result_text = "No critical clauses found."
    try:
        scan_docs = retrieve_docs(
            "Governing law, jurisdiction, term, termination, liability, obligations",
            uploaded_names
        )
        if scan_docs:
            scan_result = proactive_scan(scan_docs)
            scan_result_text = str(scan_result.content) if hasattr(scan_result, 'content') else str(scan_result)
    except Exception as e:
        scan_result_text = f"Scan failed: {str(e)}"
        
    return {
        "message": f"Successfully indexed {len(uploaded_names)} documents.",
        "filenames": uploaded_names,
        "scan_result": scan_result_text,
    }


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Run the full LangGraph multi-agent pipeline.
    
    Flow: Supervisor → [Researcher | Risk Assessor | Drafter] → Citator → Response
    """
    if not request.filenames:
        raise HTTPException(status_code=400, detail="No documents selected.")
    
    try:
        # Retrieve relevant documents from the vector store
        retrieved_docs = retrieve_docs(request.query, request.filenames)
        
        # Build the initial state for the LangGraph
        initial_state = {
            "query": request.query,
            "documents": retrieved_docs,
            "filenames": request.filenames,
            "context": "",
            "next_agent": "",
            "agent_output": "",
            "final_answer": "",
            "agent_name": "",
            "citations_verified": False,
        }
        
        # Run the full multi-agent graph
        result = legal_graph.invoke(initial_state)
        
        # Extract the final answer (Citator output takes priority)
        answer = result.get("final_answer") or result.get("agent_output", "No response generated.")
        agent_name = result.get("agent_name", "Unknown")
        citations_verified = result.get("citations_verified", False)
        
        return {
            "answer": answer,
            "agent": agent_name,
            "citations_verified": citations_verified,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
