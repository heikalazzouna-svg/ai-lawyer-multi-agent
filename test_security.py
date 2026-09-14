"""
Test script for the Presidio PII Redaction module.
Run this script to verify that sensitive information is properly scrubbed.
"""

from security import redact_pii

def test():
    sample_text = (
        "This agreement is made between John Doe and Jane Smith. "
        "John's email is john.doe@example.com and his phone number is 555-0199. "
        "The contract was signed in New York on October 5th."
    )
    
    print("--- ORIGINAL TEXT ---")
    print(sample_text)
    print("\n--- REDACTED TEXT ---")
    
    sanitized = redact_pii(sample_text)
    print(sanitized)
    
    assert "John Doe" not in sanitized, "Name was not redacted!"
    assert "john.doe@example.com" not in sanitized, "Email was not redacted!"
    assert "555-0199" not in sanitized, "Phone number was not redacted!"
    
    print("\n✅ PII Redaction is working perfectly!")

if __name__ == "__main__":
    test()
