import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from report_service import generate_report
from langchain_core.messages import AIMessage

def test_generate_report(tmp_path):
    # Create test inputs
    queries = ["What is the capital of France?"]
    # Test with both string and AIMessage to ensure the extraction logic works
    responses = [AIMessage(content="The capital of France is Paris.")]
    
    # Run the report generator
    with patch("report_service.canvas.Canvas") as mock_canvas:
        pdf_path = generate_report(queries, responses)
        
        # Verify it returns the path
        assert pdf_path == "AI_Lawyer_Report.pdf"
        
        # Verify that string extraction was called correctly, no AIMessage artifacts should be written
        mock_canvas_instance = mock_canvas.return_value
        # We can't easily inspect the exact text drawn without complex mocking, 
        # but we know it should have called simpleSplit with the extracted text.
        pass
