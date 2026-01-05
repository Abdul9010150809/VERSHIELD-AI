import re
import os
from typing import Dict, Any, List
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

class PIIRedactionAgent:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")
        self.key = os.getenv("AZURE_TEXT_ANALYTICS_KEY")
        if self.endpoint and self.key:
            self.client = TextAnalyticsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
        else:
            self.client = None

    def redact_pii(self, text: str) -> Dict[str, Any]:
        """
        Redact PII from text using Azure Text Analytics.
        Returns redacted text and list of detected PII entities.
        """
        if not self.client:
            # Fallback to regex-based redaction
            return self._regex_redaction(text)

        try:
            documents = [text]
            response = self.client.recognize_pii_entities(documents)

            redacted_text = text
            detected_entities = []

            for doc in response:
                if doc.entities:
                    for entity in doc.entities:
                        # Replace PII with redaction marker
                        redaction = f"[REDACTED-{entity.category}]"
                        redacted_text = redacted_text.replace(entity.text, redaction)
                        detected_entities.append({
                            "text": entity.text,
                            "category": entity.category,
                            "confidence": entity.confidence_score
                        })

            return {
                "redacted_text": redacted_text,
                "detected_entities": detected_entities,
                "method": "azure_ai"
            }

        except Exception as e:
            print(f"Azure PII detection failed: {e}")
            return self._regex_redaction(text)

    def _regex_redaction(self, text: str) -> Dict[str, Any]:
        """
        Fallback regex-based PII redaction.
        """
        patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
            "credit_card": r'\b\d{4}[-]?\d{4}[-]?\d{4}[-]?\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }

        redacted_text = text
        detected_entities = []

        for category, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                redaction = f"[REDACTED-{category.upper()}]"
                redacted_text = redacted_text.replace(match, redaction)
                detected_entities.append({
                    "text": match,
                    "category": category,
                    "confidence": 0.8  # Estimated confidence for regex
                })

        return {
            "redacted_text": redacted_text,
            "detected_entities": detected_entities,
            "method": "regex_fallback"
        }

    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask sensitive data in nested dictionaries.
        """
        masked_data = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Check if key suggests sensitive data
                sensitive_keys = ['email', 'phone', 'address', 'ssn', 'password', 'token', 'key']
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    masked_data[key] = "[REDACTED]"
                else:
                    # Apply PII redaction to string values
                    redaction_result = self.redact_pii(value)
                    masked_data[key] = redaction_result["redacted_text"]
            elif isinstance(value, dict):
                masked_data[key] = self.mask_sensitive_data(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self.mask_sensitive_data(item) if isinstance(item, dict) else
                    (self.redact_pii(str(item))["redacted_text"] if isinstance(item, str) else item)
                    for item in value
                ]
            else:
                masked_data[key] = value

        return masked_data