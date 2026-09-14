"""
Test script for the Hybrid Search (FAISS + BM25) implementation.
Run this script to verify that the ensemble retriever successfully
combines semantic vector search with keyword search.
"""
import os
from langchain_core.documents import Document
from vector_database import retrieve_docs, PDFS_DIRECTORY

# We need a dummy pdf to test. We'll create a fake one by just saving a text file 
# and pretending it's a PDF for the sake of the chunker, but actually our load_pdf 
# uses PDFPlumber so we need a real PDF.
# For simplicity, we'll just mock the load_pdf function in vector_database temporarily.

import vector_database
original_load_pdf = vector_database.load_pdf

def mock_load_pdf(file_path):
    return [
        Document(page_content="This is a highly semantic sentence about unforeseen acts of god and liabilities."),
        Document(page_content="The exact strict contract ID for this agreement is XQJ-992-ALPHA."),
        Document(page_content="Force Majeure clauses protect parties from liability during natural disasters.")
    ]

# Override the loader for testing
vector_database.load_pdf = mock_load_pdf

def test():
    # Create dummy pdf file so os.path.exists passes
    os.makedirs(PDFS_DIRECTORY, exist_ok=True)
    dummy_pdf_path = os.path.join(PDFS_DIRECTORY, "dummy_test.pdf")
    with open(dummy_pdf_path, "wb") as f:
        f.write(b"dummy")
        
    print("\n--- Testing Hybrid Search ---")
    
    # 1. Semantic Search (Should find the liability/force majeure docs based on meaning)
    print("\n[Query: 'What happens during a natural disaster?']")
    docs = retrieve_docs("What happens during a natural disaster?", ["dummy_test.pdf"])
    for i, doc in enumerate(docs):
        print(f"  {i+1}. {doc.page_content}")
        
    # 2. Strict Keyword Search (Should find the exact ID via BM25, even if vectors fail)
    print("\n[Query: 'XQJ-992-ALPHA']")
    docs = retrieve_docs("XQJ-992-ALPHA", ["dummy_test.pdf"])
    for i, doc in enumerate(docs):
        print(f"  {i+1}. {doc.page_content}")

    # Cleanup
    if os.path.exists(dummy_pdf_path):
        os.remove(dummy_pdf_path)
        
    print("\n✅ Hybrid Search test completed!")

if __name__ == "__main__":
    test()
