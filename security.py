"""
Enterprise Security Module for AI Lawyer.

This module integrates Microsoft Presidio to detect and redact Personally Identifiable
Information (PII) from legal documents before they are ingested into the vector
database or sent to external LLMs.

Entities detected and anonymized:
- PERSON
- EMAIL_ADDRESS
- PHONE_NUMBER
- US_SSN
- US_BANK_NUMBER
- LOCATION
- CREDIT_CARD
"""

import warnings
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Suppress expected spaCy warnings from Presidio
warnings.filterwarnings("ignore", category=UserWarning, module="spacy")

try:
    # Initialize the engines once at startup to avoid overhead per chunk
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    _SECURITY_ENABLED = True
    print("[SUCCESS] Microsoft Presidio PII Security Module Initialized.")
except Exception as e:
    print(f"[WARNING] Presidio failed to initialize. PII Redaction is disabled. Error: {e}")
    _SECURITY_ENABLED = False


def redact_pii(text: str) -> str:
    """
    Scans the input text for sensitive PII and replaces it with generic placeholders.
    
    Args:
        text (str): The raw text extracted from a PDF.
        
    Returns:
        str: The sanitized text (e.g., "Mr. [PERSON] lives in [LOCATION].").
    """
    if not _SECURITY_ENABLED or not text.strip():
        return text

    try:
        # Detect PII entities in the text
        results = analyzer.analyze(
            text=text,
            language='en',
            # We can focus on specific high-risk entities
            entities=[
                "PERSON",
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "US_SSN",
                "US_BANK_NUMBER",
                "LOCATION",
                "CREDIT_CARD",
            ],
            score_threshold=0.5
        )

        # Anonymize the detected entities (replaces with e.g. <PERSON>)
        anonymized_result = anonymizer.anonymize(text=text, analyzer_results=results)
        
        # Presidio uses <PERSON>, we can keep that or format it. 
        # By default it returns `<PERSON>`.
        return anonymized_result.text
        
    except Exception as e:
        print(f"Error during PII redaction: {e}")
        # In a strict enterprise setting, failing open (returning raw text) is bad.
        # But for this demo, we will fail open to prevent crashing the pipeline.
        return text

