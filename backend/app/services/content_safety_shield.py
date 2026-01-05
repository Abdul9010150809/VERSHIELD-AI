"""
Azure AI Content Safety Shield
Filters harmful, violent, hate speech, and inappropriate content
"""

from typing import Dict, List, Any
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import (
    AnalyzeTextOptions,
    AnalyzeImageOptions,
    TextCategory,
    ImageCategory
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import os
import base64

class ContentSafetyShield:
    """
    Azure AI Content Safety integration for real-time content filtering
    Detects: Hate, Violence, Sexual, Self-Harm content
    """
    
    # Severity levels: 0 (Safe) to 6 (Severe)
    SEVERITY_THRESHOLD = {
        "strict": 2,      # Block anything above minimal
        "moderate": 4,    # Block moderate and severe
        "permissive": 6   # Block only severe
    }
    
    def __init__(self, policy: str = "moderate"):
        """
        Initialize Content Safety client
        
        Args:
            policy: "strict", "moderate", or "permissive"
        """
        self.endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
        self.key = os.getenv("AZURE_CONTENT_SAFETY_KEY")
        self.policy = policy
        self.threshold = self.SEVERITY_THRESHOLD[policy]
        
        if self.key:
            credential = AzureKeyCredential(self.key)
        else:
            credential = DefaultAzureCredential()
        
        self.client = ContentSafetyClient(
            endpoint=self.endpoint,
            credential=credential
        )
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for harmful content
        
        Returns:
            {
                "is_safe": bool,
                "blocked_reason": str or None,
                "categories": {
                    "hate": {"severity": int, "blocked": bool},
                    "violence": {...},
                    "sexual": {...},
                    "self_harm": {...}
                },
                "overall_severity": int
            }
        """
        if not text or len(text.strip()) == 0:
            return {
                "is_safe": True,
                "blocked_reason": None,
                "categories": {},
                "overall_severity": 0
            }
        
        try:
            request = AnalyzeTextOptions(text=text)
            response = self.client.analyze_text(request)
            
            categories_result = {
                "hate": {
                    "severity": response.hate_result.severity if response.hate_result else 0,
                    "blocked": (response.hate_result.severity if response.hate_result else 0) > self.threshold
                },
                "violence": {
                    "severity": response.violence_result.severity if response.violence_result else 0,
                    "blocked": (response.violence_result.severity if response.violence_result else 0) > self.threshold
                },
                "sexual": {
                    "severity": response.sexual_result.severity if response.sexual_result else 0,
                    "blocked": (response.sexual_result.severity if response.sexual_result else 0) > self.threshold
                },
                "self_harm": {
                    "severity": response.self_harm_result.severity if response.self_harm_result else 0,
                    "blocked": (response.self_harm_result.severity if response.self_harm_result else 0) > self.threshold
                }
            }
            
            # Determine if any category is blocked
            blocked_categories = [
                cat for cat, result in categories_result.items()
                if result["blocked"]
            ]
            
            overall_severity = max(
                cat["severity"] for cat in categories_result.values()
            )
            
            return {
                "is_safe": len(blocked_categories) == 0,
                "blocked_reason": f"Content blocked due to: {', '.join(blocked_categories)}" if blocked_categories else None,
                "categories": categories_result,
                "overall_severity": overall_severity,
                "policy": self.policy,
                "threshold": self.threshold
            }
            
        except Exception as e:
            print(f"Content Safety API error: {e}")
            # Fail-open in case of service issues (configurable)
            return {
                "is_safe": True,
                "blocked_reason": None,
                "categories": {},
                "overall_severity": 0,
                "error": str(e),
                "fallback_mode": True
            }
    
    def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Analyze image for harmful visual content
        
        Args:
            image_data: Raw image bytes (JPEG, PNG, etc.)
            
        Returns:
            Similar structure to analyze_text()
        """
        try:
            # Convert to base64 for API
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            request = AnalyzeImageOptions(image={
                "content": image_b64
            })
            
            response = self.client.analyze_image(request)
            
            categories_result = {
                "hate": {
                    "severity": response.hate_result.severity if response.hate_result else 0,
                    "blocked": (response.hate_result.severity if response.hate_result else 0) > self.threshold
                },
                "violence": {
                    "severity": response.violence_result.severity if response.violence_result else 0,
                    "blocked": (response.violence_result.severity if response.violence_result else 0) > self.threshold
                },
                "sexual": {
                    "severity": response.sexual_result.severity if response.sexual_result else 0,
                    "blocked": (response.sexual_result.severity if response.sexual_result else 0) > self.threshold
                },
                "self_harm": {
                    "severity": response.self_harm_result.severity if response.self_harm_result else 0,
                    "blocked": (response.self_harm_result.severity if response.self_harm_result else 0) > self.threshold
                }
            }
            
            blocked_categories = [
                cat for cat, result in categories_result.items()
                if result["blocked"]
            ]
            
            overall_severity = max(
                cat["severity"] for cat in categories_result.values()
            )
            
            return {
                "is_safe": len(blocked_categories) == 0,
                "blocked_reason": f"Image blocked due to: {', '.join(blocked_categories)}" if blocked_categories else None,
                "categories": categories_result,
                "overall_severity": overall_severity,
                "policy": self.policy
            }
            
        except Exception as e:
            print(f"Image Content Safety error: {e}")
            return {
                "is_safe": True,
                "blocked_reason": None,
                "categories": {},
                "overall_severity": 0,
                "error": str(e),
                "fallback_mode": True
            }
    
    def analyze_combined(self, text: str = None, image_data: bytes = None) -> Dict[str, Any]:
        """
        Analyze both text and image content
        
        Returns combined safety assessment
        """
        results = {
            "is_safe": True,
            "text_result": None,
            "image_result": None,
            "blocked_reasons": []
        }
        
        if text:
            text_result = self.analyze_text(text)
            results["text_result"] = text_result
            if not text_result["is_safe"]:
                results["is_safe"] = False
                results["blocked_reasons"].append(text_result["blocked_reason"])
        
        if image_data:
            image_result = self.analyze_image(image_data)
            results["image_result"] = image_result
            if not image_result["is_safe"]:
                results["is_safe"] = False
                results["blocked_reasons"].append(image_result["blocked_reason"])
        
        return results
    
    def get_sanitized_response(self, text: str) -> str:
        """
        Return a sanitized version of text if unsafe
        
        Returns:
            "[CONTENT_BLOCKED: {reason}]" or original text if safe
        """
        result = self.analyze_text(text)
        
        if not result["is_safe"]:
            return f"[CONTENT_BLOCKED: {result['blocked_reason']}]"
        
        return text
    
    def validate_request_response(self, request_text: str, response_text: str) -> Dict[str, Any]:
        """
        Validate both request and response content
        Useful for AI-generated responses
        
        Returns:
            {
                "request_safe": bool,
                "response_safe": bool,
                "can_proceed": bool,
                "details": {...}
            }
        """
        request_result = self.analyze_text(request_text)
        response_result = self.analyze_text(response_text)
        
        return {
            "request_safe": request_result["is_safe"],
            "response_safe": response_result["is_safe"],
            "can_proceed": request_result["is_safe"] and response_result["is_safe"],
            "request_details": request_result,
            "response_details": response_result,
            "policy": self.policy
        }


class ContentSafetyMiddleware:
    """
    FastAPI middleware for automatic content filtering
    """
    
    def __init__(self, policy: str = "moderate"):
        self.shield = ContentSafetyShield(policy=policy)
    
    async def __call__(self, request, call_next):
        """
        Intercept requests and filter content
        """
        # Check request body for text content
        if request.method == "POST":
            body = await request.body()
            
            # Parse JSON and check text fields
            try:
                import json
                data = json.loads(body)
                
                # Check common text fields
                text_to_check = ""
                for field in ["text", "message", "prompt", "query", "content"]:
                    if field in data and isinstance(data[field], str):
                        text_to_check += data[field] + " "
                
                if text_to_check.strip():
                    result = self.shield.analyze_text(text_to_check)
                    
                    if not result["is_safe"]:
                        return {
                            "error": "Content blocked by safety filter",
                            "reason": result["blocked_reason"],
                            "status_code": 400
                        }
            except:
                pass  # Not JSON or parsing error - proceed
        
        # Continue with request
        response = await call_next(request)
        return response


# Example usage
if __name__ == "__main__":
    shield = ContentSafetyShield(policy="moderate")
    
    # Test harmful text
    test_cases = [
        "I want to hurt someone",
        "This is completely normal banking text",
        "Explicit sexual content here...",
        "I hate all people from XYZ group"
    ]
    
    for text in test_cases:
        result = shield.analyze_text(text)
        print(f"\nText: {text[:50]}...")
        print(f"Safe: {result['is_safe']}")
        if not result['is_safe']:
            print(f"Reason: {result['blocked_reason']}")
        print(f"Overall Severity: {result['overall_severity']}")
