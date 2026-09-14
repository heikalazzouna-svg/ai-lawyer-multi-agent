"""
Agent Node Functions for the AI Lawyer LangGraph.

Each function takes the current graph state, performs its specialized task,
and returns an updated state dict. These are pure functions with no side effects,
making them easy to test and debug independently.
"""

import os
from typing import TypedDict, Annotated
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv

from agents.prompts import (
    SUPERVISOR_PROMPT,
    RESEARCHER_PROMPT,
    RISK_ASSESSOR_PROMPT,
    DRAFTER_PROMPT,
    CITATOR_PROMPT,
    COMPARATOR_PROMPT,
)

load_dotenv()


# ─── Shared State Definition ─────────────────────────────────────────────────

class AgentState(TypedDict):
    """
    The shared state that flows through every node in the LangGraph.
    
    Fields:
        query: The user's original question.
        documents: Retrieved LangChain Document objects.
        filenames: List of uploaded PDF filenames for retrieval filtering.
        context: The formatted context string (with page metadata).
        next_agent: The agent the Supervisor decided should handle this query.
        agent_output: The raw output from the specialist agent.
        final_answer: The citator-verified final response.
        agent_name: Human-readable name of the agent that handled the query.
        citations_verified: Whether the Citator confirmed all citations.
    """
    query: str
    documents: list[Document]
    filenames: list[str]
    context: str
    next_agent: str
    agent_output: str
    final_answer: str
    agent_name: str
    citations_verified: bool


# ─── LLM Factory ─────────────────────────────────────────────────────────────

def _get_llm() -> ChatGroq:
    """Create a fresh LLM instance for each agent call."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set.")
    model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
    return ChatGroq(model=model_name)


def _get_streaming_llm() -> ChatGroq:
    """Create a streaming LLM instance that yields tokens incrementally."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set.")
    model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
    return ChatGroq(model=model_name, streaming=True)


def _format_context(documents: list[Document]) -> str:
    """Format retrieved documents with source and page metadata."""
    blocks = []
    for doc in documents:
        page_num = doc.metadata.get('page', 0) + 1
        source = doc.metadata.get('source', 'Unknown')
        blocks.append(f"--- Source: {source}, Page: {page_num} ---\n{doc.page_content}")
    return "\n\n".join(blocks)


# ─── Node: Supervisor ────────────────────────────────────────────────────────

def supervisor_node(state: AgentState) -> dict:
    """
    Classifies the user's intent and decides which specialist agent to invoke.
    This is the entry point of the graph.
    """
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_template(SUPERVISOR_PROMPT)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"query": state["query"]})
        classification = response.content.strip().lower()
        
        # Normalize the classification to a known agent
        valid_agents = {"comparator", "researcher", "risk_assessor", "drafter", "general"}
        if classification not in valid_agents:
            classification = "researcher"  # Default fallback
            
    except Exception:
        classification = "researcher"  # Safe fallback on error
    
    # Also build the context string here so downstream agents have it ready
    context = _format_context(state.get("documents", []))
    
    return {
        "next_agent": classification,
        "context": context,
    }


# ─── Node: Legal Researcher ──────────────────────────────────────────────────

def researcher_node(state: AgentState) -> dict:
    """
    Deep document Q&A with strict page-level citations.
    Now equipped with Web Search tools for external case law lookup!
    """
    llm = _get_llm()
    search = DuckDuckGoSearchRun()
    
    # Equip the LLM with the search tool
    llm_with_tools = llm.bind_tools([search])
    
    try:
        # Pass 1: Ask the LLM if it wants to search the web for external legal precedents
        initial_msg = llm_with_tools.invoke([
            ("system", "You are a Legal Researcher. You have access to a web search tool (DuckDuckGo). If the user asks about real-world case law, precedents, or statutes NOT found in the uploaded documents, use the search tool. Otherwise, just answer the question normally. Context: " + state["context"]),
            ("human", state["query"])
        ])
        
        if initial_msg.tool_calls:
            # The agent autonomously decided to use the search tool!
            tool_call = initial_msg.tool_calls[0]
            # Handle both "query" and "title" args which DuckDuckGo might expect depending on langchain version
            search_query = tool_call["args"].get("query", tool_call["args"].get("title", state["query"]))
            
            try:
                search_results = search.invoke(search_query)
            except Exception:
                search_results = "Web search failed or was rate limited."
            
            # Pass 2: Generate the final answer including the web search results
            enhanced_prompt = ChatPromptTemplate.from_template(
                RESEARCHER_PROMPT + "\n\n--- External Web Search Results ---\n{search_results}\n\n*Note: Incorporate these external findings into your answer where relevant.*"
            )
            response = (enhanced_prompt | llm).invoke({
                "query": state["query"],
                "context": state["context"],
                "search_results": search_results
            })
            output = response.content
        else:
            # Standard path (no tool used)
            prompt = ChatPromptTemplate.from_template(RESEARCHER_PROMPT)
            response = (prompt | llm).invoke({
                "query": state["query"],
                "context": state["context"],
            })
            output = response.content
            
    except Exception as e:
        output = f"Research agent error: {str(e)}"
    
    return {
        "agent_output": output,
        "agent_name": "Legal Researcher",
    }


# ─── Node: Risk Assessor ─────────────────────────────────────────────────────

def risk_assessor_node(state: AgentState) -> dict:
    """
    Scans documents for legal risks, missing clauses, and unfavorable terms.
    Returns a structured risk report with severity ratings.
    """
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_template(RISK_ASSESSOR_PROMPT)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "query": state["query"],
            "context": state["context"],
        })
        output = response.content
    except Exception as e:
        output = f"Risk assessment error: {str(e)}"
    
    return {
        "agent_output": output,
        "agent_name": "Risk Assessor",
    }


# ─── Node: Drafter ───────────────────────────────────────────────────────────

def drafter_node(state: AgentState) -> dict:
    """
    Generates professional legal memos, summaries, and client-ready documents.
    """
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_template(DRAFTER_PROMPT)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "query": state["query"],
            "context": state["context"],
        })
        output = response.content
    except Exception as e:
        output = f"Drafting error: {str(e)}"
    
    return {
        "agent_output": output,
        "agent_name": "Legal Drafter",
    }


# ─── Node: Contract Comparator ───────────────────────────────────────────────

def comparator_node(state: AgentState) -> dict:
    """
    Compares multiple legal documents side-by-side to find differences,
    similarities, and inconsistencies.
    """
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_template(COMPARATOR_PROMPT)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "query": state["query"],
            "context": state["context"],
        })
        output = response.content
    except Exception as e:
        output = f"Comparison error: {str(e)}"
    
    return {
        "agent_output": output,
        "agent_name": "Contract Comparator",
    }


# ─── Node: General (Fallback) ────────────────────────────────────────────────

def general_node(state: AgentState) -> dict:
    """
    Handles greetings, off-topic queries, and unclear requests.
    """
    return {
        "agent_output": (
            "Hello! I'm the AI Lawyer multi-agent system. I can help you with:\n\n"
            "🔍 **Legal Research** — Ask me factual questions about your documents\n"
            "⚠️ **Risk Assessment** — Ask me to review contracts for risks and red flags\n"
            "📝 **Legal Drafting** — Ask me to draft memos, summaries, or client emails\n\n"
            "Please upload a legal document and ask a specific question to get started."
        ),
        "agent_name": "Assistant",
        "final_answer": "",
        "citations_verified": True,
    }


# ─── Node: Citator (Quality Gate) ────────────────────────────────────────────

def citator_node(state: AgentState) -> dict:
    """
    Final validation pass. Reviews the specialist agent's output and verifies
    that every claim has a proper citation. This is the quality gate that
    prevents hallucinated citations from reaching the user.
    """
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_template(CITATOR_PROMPT)
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "agent_output": state["agent_output"],
            "context": state["context"],
        })
        verified_output = response.content
        citations_ok = "all citations verified" in verified_output.lower()
    except Exception:
        # If citator fails, pass through the original output
        verified_output = state["agent_output"]
        citations_ok = False
    
    return {
        "final_answer": verified_output,
        "citations_verified": citations_ok,
    }
