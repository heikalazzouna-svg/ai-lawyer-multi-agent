"""
LangGraph State Graph Definition for the AI Lawyer Multi-Agent System.

This module defines the directed graph that orchestrates the flow between
the Supervisor, specialist agents (Researcher, Risk Assessor, Drafter),
and the Citator quality gate.

Architecture:
    START → Supervisor → [Researcher | Risk Assessor | Drafter | General] → Citator → END
"""

from langgraph.graph import StateGraph, START, END

from agents.nodes import (
    AgentState,
    supervisor_node,
    researcher_node,
    risk_assessor_node,
    drafter_node,
    comparator_node,
    general_node,
    citator_node,
)


def _route_after_supervisor(state: AgentState) -> str:
    """
    Conditional edge function.
    Routes from the Supervisor to the appropriate specialist agent
    based on the classified intent.
    """
    next_agent = state.get("next_agent", "researcher")
    
    routing_map = {
        "comparator": "comparator",
        "researcher": "researcher",
        "risk_assessor": "risk_assessor",
        "drafter": "drafter",
        "general": "general",
    }
    
    return routing_map.get(next_agent, "researcher")


def _route_after_specialist(state: AgentState) -> str:
    """
    Routes from specialist agents to the Citator, 
    or directly to END for the general/fallback agent.
    """
    if state.get("agent_name") == "Assistant":
        return END
    return "citator"


def create_legal_agent_graph() -> StateGraph:
    """
    Build and compile the complete LangGraph for the AI Lawyer.
    
    Returns:
        A compiled StateGraph ready to be invoked with .invoke()
    """
    # ── Define the graph ──────────────────────────────────────────────────
    workflow = StateGraph(AgentState)
    
    # ── Add all agent nodes ───────────────────────────────────────────────
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("comparator", comparator_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("risk_assessor", risk_assessor_node)
    workflow.add_node("drafter", drafter_node)
    workflow.add_node("general", general_node)
    workflow.add_node("citator", citator_node)
    
    # ── Define edges ──────────────────────────────────────────────────────
    
    # Entry point: always start with the Supervisor
    workflow.add_edge(START, "supervisor")
    
    # Supervisor routes to the correct specialist via conditional edge
    workflow.add_conditional_edges(
        "supervisor",
        _route_after_supervisor,
        {
            "comparator": "comparator",
            "researcher": "researcher",
            "risk_assessor": "risk_assessor",
            "drafter": "drafter",
            "general": "general",
        }
    )
    
    # Each specialist routes to the Citator (except General which goes to END)
    workflow.add_conditional_edges("comparator", _route_after_specialist)
    workflow.add_conditional_edges("researcher", _route_after_specialist)
    workflow.add_conditional_edges("risk_assessor", _route_after_specialist)
    workflow.add_conditional_edges("drafter", _route_after_specialist)
    workflow.add_conditional_edges("general", _route_after_specialist)
    
    # Citator is the final node before END
    workflow.add_edge("citator", END)
    
    # ── Compile and return ────────────────────────────────────────────────
    compiled_graph = workflow.compile()
    
    return compiled_graph
