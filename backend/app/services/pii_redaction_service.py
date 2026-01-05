"""
Real-Time PII Redaction & Masking Service
Uses Azure AI Language for entity recognition and custom patterns
"""

import re
import hashlib
from typing import Dict, List, Any, Tuple
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import os

class PIIRedactionService:
    """
    Detects and redacts PII (Personally Identifiable Information) in real-time
    Supports: SSN, Credit Cards, Email, Phone, Addresses, Names, etc.
    """
    
    # PII Categories supported by Azure AI Language
    PII_CATEGORIES = [
        "Person",
        "PersonType", 
        "PhoneNumber",
        "Email",
        "URL",
        "IPAddress",
        "DateTime",
        "Quantity",
        "Organization",
        "Address",
        "CreditCard",
        "InternationalBankingAccountNumber",
        "ABARoutingNumber",
        "SWIFTCode",
        "USSocialSecurityNumber",
        "USDriversLicenseNumber",
        "USPassportNumber"
    ]
    
    def __init__(self):
        """Initialize Azure AI Language client"""
        self.endpoint = os.getenv("AZURE_AI_LANGUAGE_ENDPOINT")
        self.key = os.getenv("AZURE_AI_LANGUAGE_KEY")
        
        if self.key:
            credential = AzureKeyCredential(self.key)
        else:
            # Use Managed Identity in production
            credential = DefaultAzureCredential()
        
        self.client = TextAnalyticsClient(
            endpoint=self.endpoint,
            credential=credential
        )
        
        # Regex patterns for additional PII detection
        self.custom_patterns = {
            "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "credit_card": re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
            "bank_account": re.compile(r'\b\d{10,17}\b'),
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b(\+\d{1,2}\s?)?(\()?\d{3}(\))?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
            "ip_address": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
        }
        
    def redact_text(self, text: str, redaction_mode: str = "hash") -> Dict[str, Any]:
        """
        Redact PII from text using Azure AI + custom patterns
        
        Args:
            text: Input text to redact
            redaction_mode: "hash", "mask", or "remove"
            
        Returns:
            {
                "redacted_text": str,
                "entities_found": List[Dict],
                "redaction_count": int,
                "original_hash": str
            }
        """
        if not text or len(text.strip()) == 0:
            return {
                "redacted_text": text,
                "entities_found": [],
                "redaction_count": 0,
                "original_hash": ""
            }
        
        # Store original hash for audit trail
        original_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Detect PII using Azure AI Language
        try:
            response = self.client.recognize_pii_entities(
                documents=[text],
                language="en",
                categories_filter=self.PII_CATEGORIES
            )
            
            entities_found = []
            redacted_text = text
            
            for doc in response:
                if not doc.is_error:
                    # Sort entities by offset (descending) to avoid index shifting
                    sorted_entities = sorted(
                        doc.entities,
                        key=lambda e: e.offset,
                        reverse=True
                    )
                    
                    for entity in sorted_entities:
                        entities_found.append({
                            "text": entity.text,
                            "category": entity.category,
                            "subcategory": entity.subcategory,
                            "confidence_score": entity.confidence_score,
                            "offset": entity.offset,
                            "length": entity.length
                        })
                        
                        # Redact based on mode
                        replacement = self._get_replacement(
                            entity.text,
                            entity.category,
                            redaction_mode
                        )
                        
                        # Replace in text
                        start = entity.offset
                        end = entity.offset + entity.length
                        redacted_text = (
                            redacted_text[:start] + 
                            replacement + 
                            redacted_text[end:]
                        )
            
            # Apply custom regex patterns for additional coverage
            redacted_text, custom_entities = self._apply_custom_patterns(
                redacted_text,
                redaction_mode
            )
            entities_found.extend(custom_entities)
            
            return {
                "redacted_text": redacted_text,
                "entities_found": entities_found,
                "redaction_count": len(entities_found),
                "original_hash": original_hash,
                "redaction_mode": redaction_mode
            }
            
        except Exception as e:
            # Fallback to regex-only if Azure service fails
            print(f"Azure AI Language error: {e}. Falling back to regex patterns.")
            redacted_text, entities_found = self._apply_custom_patterns(text, redaction_mode)
            
            return {
                "redacted_text": redacted_text,
                "entities_found": entities_found,
                "redaction_count": len(entities_found),
                "original_hash": original_hash,
                "redaction_mode": redaction_mode,
                "fallback_mode": True
            }
    
    def _get_replacement(self, original_text: str, category: str, mode: str) -> str:
        """Generate replacement text based on redaction mode"""
        if mode == "hash":
            # Use deterministic hash for consistency
            text_hash = hashlib.sha256(original_text.encode()).hexdigest()[:8]
            return f"[{category.upper()}_{text_hash}]"
        elif mode == "mask":
            # Mask with asterisks (preserve length)
            return "*" * len(original_text)
        elif mode == "remove":
            return f"[{category.upper()}_REDACTED]"
        else:
            return "[REDACTED]"
    
    def _apply_custom_patterns(self, text: str, mode: str) -> Tuple[str, List[Dict]]:
        """Apply regex patterns for additional PII detection"""
        entities_found = []
        redacted_text = text
        
        for pattern_name, pattern in self.custom_patterns.items():
            matches = list(pattern.finditer(redacted_text))
            
            # Process in reverse order to avoid index issues
            for match in reversed(matches):
                entities_found.append({
                    "text": match.group(),
                    "category": pattern_name,
                    "subcategory": None,
                    "confidence_score": 1.0,  # Regex is deterministic
                    "offset": match.start(),
                    "length": len(match.group()),
                    "source": "custom_regex"
                })
                
                replacement = self._get_replacement(
                    match.group(),
                    pattern_name,
                    mode
                )
                
                redacted_text = (
                    redacted_text[:match.start()] + 
                    replacement + 
                    redacted_text[match.end():]
                )
        
        return redacted_text, entities_found
    
    def redact_json(self, data: Dict[str, Any], fields_to_redact: List[str]) -> Dict[str, Any]:
        """
        Redact specific fields in a JSON object
        
        Args:
            data: Input JSON object
            fields_to_redact: List of field names to redact
            
        Returns:
            Redacted JSON object with audit trail
        """
        redacted_data = data.copy()
        redaction_log = []
        
        for field in fields_to_redact:
            if field in redacted_data and isinstance(redacted_data[field], str):
                result = self.redact_text(redacted_data[field])
                redacted_data[field] = result["redacted_text"]
                
                if result["redaction_count"] > 0:
                    redaction_log.append({
                        "field": field,
                        "redaction_count": result["redaction_count"],
                        "entities": result["entities_found"]
                    })
        
        redacted_data["_redaction_metadata"] = {
            "redacted_fields": fields_to_redact,
            "redaction_log": redaction_log,
            "timestamp": "2026-01-05T00:00:00Z"
        }
        
        return redacted_data
    
    def validate_pii_free(self, text: str, threshold: float = 0.8) -> Dict[str, Any]:
        """
        Validate that text is PII-free (useful for testing)
        
        Returns:
            {
                "is_pii_free": bool,
                "confidence": float,
                "violations": List[Dict]
            }
        """
        result = self.redact_text(text, redaction_mode="hash")
        
        high_confidence_violations = [
            entity for entity in result["entities_found"]
            if entity.get("confidence_score", 1.0) >= threshold
        ]
        
        return {
            "is_pii_free": len(high_confidence_violations) == 0,
            "confidence": 1.0 - (len(high_confidence_violations) / max(len(result["entities_found"]), 1)),
            "violations": high_confidence_violations,
            "total_entities": len(result["entities_found"])
        }


# Example usage
if __name__ == "__main__":
    # Mock test (Azure credentials required in production)
    service = PIIRedactionService()
    
    test_text = """
    Hi, my name is John Doe. My SSN is 123-45-6789 and my credit card is 4532-1234-5678-9010.
    You can reach me at john.doe@example.com or call 555-123-4567.
    My bank account is 1234567890 and I live at 123 Main St, New York, NY 10001.
    """
    
    result = service.redact_text(test_text, redaction_mode="hash")
    print(f"Redacted Text:\n{result['redacted_text']}\n")
    print(f"Entities Found: {result['redaction_count']}")
    print(f"Original Hash: {result['original_hash']}")
