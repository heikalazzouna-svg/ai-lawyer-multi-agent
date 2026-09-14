"""
AI Lawyer — Multi-Agent LangGraph System

This package contains the agentic orchestration layer:
- graph.py    → The compiled LangGraph StateGraph
- nodes.py    → Individual agent node functions
- prompts.py  → Centralized prompt library for all agents
"""

from agents.graph import create_legal_agent_graph
