"""
Unit Tests for the AI Lawyer Multi-Agent System.

Tests that the Supervisor correctly classifies intent and routes to
the appropriate specialist agent, and that each agent produces
properly formatted output.
"""

import pytest
from unittest.mock import patch
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from agents.nodes import (
    AgentState,
    supervisor_node,
    researcher_node,
    risk_assessor_node,
    drafter_node,
    general_node,
    citator_node,
    _format_context,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_state() -> AgentState:
    """A minimal valid agent state for testing."""
    return {
        "query": "What does Article 5 say?",
        "documents": [],
        "filenames": ["test.pdf"],
        "context": "--- Source: test.pdf, Page: 1 ---\nArticle 5: Everyone has the right to life.",
        "next_agent": "",
        "agent_output": "",
        "final_answer": "",
        "agent_name": "",
        "citations_verified": False,
    }


def create_mock_llm(content: str):
    """Creates a LangChain Runnable that returns an AIMessage with the given content."""
    mock_response = AIMessage(content=content)
    return RunnableLambda(lambda x: mock_response)

def create_error_llm(error: Exception):
    """Creates a LangChain Runnable that raises the given exception."""
    def _raise_err(x):
        raise error
    return RunnableLambda(_raise_err)


# ─── Test: Context Formatting ─────────────────────────────────────────────────

class TestFormatContext:
    def test_formats_with_page_metadata(self):
        """Context should include source filename and page number."""
        from langchain_core.documents import Document
        
        docs = [
            Document(page_content="Article 1 text", metadata={"source": "contract.pdf", "page": 0}),
            Document(page_content="Article 2 text", metadata={"source": "contract.pdf", "page": 1}),
        ]
        
        result = _format_context(docs)
        
        assert "Source: contract.pdf, Page: 1" in result
        assert "Source: contract.pdf, Page: 2" in result
        assert "Article 1 text" in result
        assert "Article 2 text" in result

    def test_empty_documents(self):
        """Should handle empty document list gracefully."""
        result = _format_context([])
        assert result == ""


# ─── Test: Supervisor Routing ──────────────────────────────────────────────────

class TestSupervisorNode:
    @patch("agents.nodes._get_llm")
    def test_routes_to_researcher(self, mock_get_llm, sample_state):
        """Research questions should route to the researcher agent."""
        mock_get_llm.return_value = create_mock_llm("researcher")

        result = supervisor_node(sample_state)
        
        assert result["next_agent"] == "researcher"

    @patch("agents.nodes._get_llm")
    def test_routes_to_risk_assessor(self, mock_get_llm, sample_state):
        """Risk-related queries should route to the risk assessor."""
        mock_get_llm.return_value = create_mock_llm("risk_assessor")
        
        sample_state["query"] = "Are there any risks in this contract?"
        result = supervisor_node(sample_state)
        
        assert result["next_agent"] == "risk_assessor"

    @patch("agents.nodes._get_llm")
    def test_routes_to_drafter(self, mock_get_llm, sample_state):
        """Drafting requests should route to the drafter agent."""
        mock_get_llm.return_value = create_mock_llm("drafter")
        
        sample_state["query"] = "Draft a summary email for my client"
        result = supervisor_node(sample_state)
        
        assert result["next_agent"] == "drafter"

    @patch("agents.nodes._get_llm")
    def test_defaults_to_researcher_on_unknown(self, mock_get_llm, sample_state):
        """Unknown classifications should fall back to researcher."""
        mock_get_llm.return_value = create_mock_llm("unknown_agent_xyz")
        
        result = supervisor_node(sample_state)
        
        assert result["next_agent"] == "researcher"

    @patch("agents.nodes._get_llm")
    def test_defaults_to_researcher_on_error(self, mock_get_llm, sample_state):
        """LLM errors should fall back to researcher."""
        mock_get_llm.return_value = create_error_llm(Exception("API Error"))
        
        result = supervisor_node(sample_state)
        
        assert result["next_agent"] == "researcher"


# ─── Test: Specialist Agents ──────────────────────────────────────────────────

class TestResearcherNode:
    @patch("agents.nodes._get_llm")
    def test_returns_output_and_agent_name(self, mock_get_llm, sample_state):
        """Researcher should return agent_output and correct agent_name."""
        mock_get_llm.return_value = create_mock_llm("Article 5 guarantees the right to life [test.pdf, Page 1].")
        
        result = researcher_node(sample_state)
        
        assert result["agent_name"] == "Legal Researcher"
        assert "Article 5" in result["agent_output"]


class TestRiskAssessorNode:
    @patch("agents.nodes._get_llm")
    def test_returns_risk_assessment(self, mock_get_llm, sample_state):
        """Risk assessor should return agent_name as 'Risk Assessor'."""
        mock_get_llm.return_value = create_mock_llm("🔴 HIGH: No limitation of liability clause found.")
        
        result = risk_assessor_node(sample_state)
        
        assert result["agent_name"] == "Risk Assessor"
        assert "HIGH" in result["agent_output"]


class TestDrafterNode:
    @patch("agents.nodes._get_llm")
    def test_returns_draft(self, mock_get_llm, sample_state):
        """Drafter should return agent_name as 'Legal Drafter'."""
        mock_get_llm.return_value = create_mock_llm("Dear Client, please find the summary below...")
        
        result = drafter_node(sample_state)
        
        assert result["agent_name"] == "Legal Drafter"
        assert "Client" in result["agent_output"]


class TestGeneralNode:
    def test_returns_capabilities_overview(self, sample_state):
        """General node should return a capabilities message without LLM call."""
        result = general_node(sample_state)
        
        assert result["agent_name"] == "Assistant"
        assert "Legal Research" in result["agent_output"]
        assert result["citations_verified"] is True


# ─── Test: Citator Quality Gate ────────────────────────────────────────────────

class TestCitatorNode:
    @patch("agents.nodes._get_llm")
    def test_marks_verified_when_all_citations_valid(self, mock_get_llm, sample_state):
        """Citator should set citations_verified=True when all checks pass."""
        mock_get_llm.return_value = create_mock_llm("Article 5 says X [test.pdf, Page 1].\n\n✅ All citations verified")
        
        sample_state["agent_output"] = "Article 5 says X [test.pdf, Page 1]."
        result = citator_node(sample_state)
        
        assert result["citations_verified"] is True
        assert result["final_answer"] != ""

    @patch("agents.nodes._get_llm")
    def test_passes_through_on_error(self, mock_get_llm, sample_state):
        """Citator should pass through original output if it fails."""
        mock_get_llm.return_value = create_error_llm(Exception("API Error"))
        
        sample_state["agent_output"] = "Original output"
        result = citator_node(sample_state)
        
        assert result["final_answer"] == "Original output"
        assert result["citations_verified"] is False


# ─── Test: Graph Compilation ──────────────────────────────────────────────────

class TestGraphCompilation:
    def test_graph_compiles_successfully(self):
        """The LangGraph should compile without errors."""
        from agents.graph import create_legal_agent_graph
        
        graph = create_legal_agent_graph()
        assert graph is not None
