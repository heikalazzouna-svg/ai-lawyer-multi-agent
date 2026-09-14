"""
Streaming Pipeline for the AI Lawyer Multi-Agent System.

This module provides an async generator that orchestrates the full
multi-agent pipeline (Supervisor → Specialist → Citator) while
emitting Server-Sent Events (SSE) at each stage.

The specialist agent streams tokens in real-time via Groq's native
streaming API, giving users a ChatGPT-like experience.
"""

import json
import time
from typing import AsyncGenerator

from langchain_core.prompts import ChatPromptTemplate

from agents.nodes import (
    AgentState,
    _get_llm,
    _get_streaming_llm,
    _format_context,
    general_node,
)
from agents.prompts import (
    SUPERVISOR_PROMPT,
    RESEARCHER_PROMPT,
    RISK_ASSESSOR_PROMPT,
    DRAFTER_PROMPT,
    CITATOR_PROMPT,
    COMPARATOR_PROMPT,
)


# ─── Agent Display Names ─────────────────────────────────────────────────────

AGENT_DISPLAY_NAMES = {
    "comparator": "Contract Comparator",
    "researcher": "Legal Researcher",
    "risk_assessor": "Risk Assessor",
    "drafter": "Legal Drafter",
    "general": "Assistant",
}

AGENT_PROMPTS = {
    "comparator": COMPARATOR_PROMPT,
    "researcher": RESEARCHER_PROMPT,
    "risk_assessor": RISK_ASSESSOR_PROMPT,
    "drafter": DRAFTER_PROMPT,
}


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_legal_pipeline(state: AgentState) -> AsyncGenerator[str, None]:
    """
    Async generator that runs the full multi-agent pipeline and yields
    SSE-formatted events at each stage.

    Events emitted:
        trace   — Agent status updates (started, completed, routing info)
        token   — Individual text chunks from the streaming specialist
        done    — Final result with agent name and citation status
        error   — Error information if something goes wrong
    """

    # ── Stage 1: Supervisor ───────────────────────────────────────────────
    yield _sse_event("trace", {
        "node": "supervisor",
        "status": "running",
        "label": "Classifying intent...",
    })

    t0 = time.time()

    try:
        llm = _get_llm()
        prompt = ChatPromptTemplate.from_template(SUPERVISOR_PROMPT)
        chain = prompt | llm

        response = chain.invoke({"query": state["query"]})
        classification = response.content.strip().lower()

        valid_agents = {"comparator", "researcher", "risk_assessor", "drafter", "general"}
        if classification not in valid_agents:
            classification = "researcher"
    except Exception:
        classification = "researcher"

    # Build the context
    context = _format_context(state.get("documents", []))
    state["next_agent"] = classification
    state["context"] = context

    elapsed_supervisor = round(time.time() - t0, 1)

    agent_display = AGENT_DISPLAY_NAMES.get(classification, "Legal Researcher")

    yield _sse_event("trace", {
        "node": "supervisor",
        "status": "done",
        "next_agent": classification,
        "agent_display": agent_display,
        "elapsed": elapsed_supervisor,
    })

    # ── Stage 2: Specialist Agent ─────────────────────────────────────────

    # Handle "general" (no-LLM fallback) separately
    if classification == "general":
        result = general_node(state)
        state.update(result)

        yield _sse_event("trace", {
            "node": "specialist",
            "agent": "Assistant",
            "status": "done",
            "elapsed": 0,
        })

        # Emit the full output as a single token event
        yield _sse_event("token", {"chunk": state["agent_output"]})

        yield _sse_event("done", {
            "agent": "Assistant",
            "citations_verified": True,
            "final_answer": state["agent_output"],
        })
        return

    # For real specialist agents, stream tokens
    yield _sse_event("trace", {
        "node": "specialist",
        "agent": agent_display,
        "status": "running",
        "label": f"{agent_display} analyzing documents...",
    })

    t1 = time.time()
    specialist_prompt_template = AGENT_PROMPTS.get(classification, RESEARCHER_PROMPT)

    try:
        streaming_llm = _get_streaming_llm()
        prompt = ChatPromptTemplate.from_template(specialist_prompt_template)
        chain = prompt | streaming_llm

        full_output = ""
        for chunk in chain.stream({
            "query": state["query"],
            "context": state["context"],
        }):
            token_text = chunk.content if hasattr(chunk, 'content') else str(chunk)
            if token_text:
                full_output += token_text
                yield _sse_event("token", {"chunk": token_text})

        state["agent_output"] = full_output
        state["agent_name"] = agent_display

    except Exception as e:
        error_msg = f"Agent error: {str(e)}"
        state["agent_output"] = error_msg
        state["agent_name"] = agent_display
        yield _sse_event("token", {"chunk": error_msg})

    elapsed_specialist = round(time.time() - t1, 1)

    yield _sse_event("trace", {
        "node": "specialist",
        "agent": agent_display,
        "status": "done",
        "elapsed": elapsed_specialist,
    })

    # ── Stage 3: Citator ──────────────────────────────────────────────────
    yield _sse_event("trace", {
        "node": "citator",
        "status": "running",
        "label": "Verifying citations...",
    })

    t2 = time.time()

    try:
        llm = _get_llm()
        prompt = ChatPromptTemplate.from_template(CITATOR_PROMPT)
        chain = prompt | llm

        response = chain.invoke({
            "agent_output": state["agent_output"],
            "context": state["context"],
        })
        verified_output = response.content
        citations_ok = "all citations verified" in verified_output.lower()
    except Exception:
        verified_output = state["agent_output"]
        citations_ok = False

    elapsed_citator = round(time.time() - t2, 1)

    yield _sse_event("trace", {
        "node": "citator",
        "status": "done",
        "elapsed": elapsed_citator,
        "verified": citations_ok,
    })

    # ── Final Event ───────────────────────────────────────────────────────
    yield _sse_event("done", {
        "agent": agent_display,
        "citations_verified": citations_ok,
        "final_answer": verified_output,
    })
