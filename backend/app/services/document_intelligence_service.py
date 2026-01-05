"""
Automated Document Intelligence Extraction Service
Uses Azure Document Intelligence for OCR, form recognition, and entity extraction
"""

from typing import Dict, List, Any, Optional
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import os
import base64
import json

class DocumentIntelligenceService:
    """
    Azure Document Intelligence for automated document processing
    """

    def __init__(self):
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

        if self.key:
            credential = AzureKeyCredential(self.key)
        else:
            credential = DefaultAzureCredential()

        self.client = DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=credential
        )

        # Prebuilt models
        self.models = {
            "prebuilt-read": "prebuilt-read",  # General document reading
            "prebuilt-layout": "prebuilt-layout",  # Document layout analysis
            "prebuilt-document": "prebuilt-document",  # General document
            "prebuilt-invoice": "prebuilt-invoice",  # Invoice processing
            "prebuilt-receipt": "prebuilt-receipt",  # Receipt processing
            "prebuilt-idDocument": "prebuilt-idDocument",  # ID documents
            "prebuilt-businessCard": "prebuilt-businessCard",  # Business cards
            "prebuilt-contract": "prebuilt-contract"  # Contract analysis
        }

    def analyze_document(self, document_data: bytes, model: str = "prebuilt-read",
                        pages: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze document using specified model

        Args:
            document_data: Raw document bytes
            model: Model to use for analysis
            pages: Specific pages to analyze (e.g., "1,2,3" or "1-3")

        Returns:
            Extracted document information
        """
        try:
            # Convert to base64
            document_b64 = base64.b64encode(document_data).decode('utf-8')

            # Prepare request
            request = AnalyzeDocumentRequest(
                base64_source=document_b64
            )

            # Analyze document
            poller = self.client.begin_analyze_document(
                model_id=model,
                analyze_request=request,
                pages=pages
            )

            result = poller.result()

            # Extract information
            extracted_data = self._extract_result_data(result)

            return {
                "success": True,
                "model_used": model,
                "pages_analyzed": len(result.pages) if result.pages else 0,
                "content": result.content,
                "entities": extracted_data.get("entities", []),
                "key_value_pairs": extracted_data.get("key_value_pairs", {}),
                "tables": extracted_data.get("tables", []),
                "styles": extracted_data.get("styles", []),
                "languages": extracted_data.get("languages", [])
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_used": model
            }

    def _extract_result_data(self, result: AnalyzeResult) -> Dict[str, Any]:
        """Extract structured data from analysis result"""
        data = {
            "entities": [],
            "key_value_pairs": {},
            "tables": [],
            "styles": [],
            "languages": []
        }

        # Extract entities
        if result.entities:
            for entity in result.entities:
                data["entities"].append({
                    "category": entity.category,
                    "subcategory": entity.subcategory,
                    "content": entity.content,
                    "confidence": entity.confidence,
                    "bounding_regions": [
                        {
                            "page_number": region.page_number,
                            "bounding_box": region.bounding_box
                        } for region in entity.bounding_regions
                    ] if entity.bounding_regions else []
                })

        # Extract key-value pairs
        if result.key_value_pairs:
            for kvp in result.key_value_pairs:
                if kvp.key and kvp.value:
                    key = kvp.key.content if kvp.key.content else ""
                    value = kvp.value.content if kvp.value.content else ""
                    confidence = kvp.confidence
                    data["key_value_pairs"][key] = {
                        "value": value,
                        "confidence": confidence
                    }

        # Extract tables
        if result.tables:
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }

                if table.cells:
                    for cell in table.cells:
                        table_data["cells"].append({
                            "row_index": cell.row_index,
                            "column_index": cell.column_index,
                            "content": cell.content,
                            "bounding_regions": [
                                {
                                    "page_number": region.page_number,
                                    "bounding_box": region.bounding_box
                                } for region in cell.bounding_regions
                            ] if cell.bounding_regions else []
                        })

                data["tables"].append(table_data)

        # Extract styles
        if result.styles:
            for style in result.styles:
                data["styles"].append({
                    "confidence": style.confidence,
                    "color": style.color,
                    "background_color": style.background_color,
                    "is_handwritten": style.is_handwritten
                })

        # Extract languages
        if result.languages:
            for lang in result.languages:
                data["languages"].append({
                    "locale": lang.locale,
                    "confidence": lang.confidence
                })

        return data

    def extract_text(self, document_data: bytes) -> Dict[str, Any]:
        """
        Simple text extraction from document

        Returns:
            {"text": extracted_text, "confidence": avg_confidence}
        """
        result = self.analyze_document(document_data, model="prebuilt-read")

        if result["success"]:
            return {
                "text": result.get("content", ""),
                "confidence": 0.95,  # Placeholder
                "pages": result.get("pages_analyzed", 0)
            }
        else:
            return {
                "text": "",
                "confidence": 0.0,
                "error": result.get("error", "Extraction failed")
            }

    def extract_invoice_data(self, document_data: bytes) -> Dict[str, Any]:
        """
        Extract structured data from invoice

        Returns:
            Invoice fields like vendor, amount, date, etc.
        """
        result = self.analyze_document(document_data, model="prebuilt-invoice")

        if not result["success"]:
            return {"error": result.get("error", "Invoice analysis failed")}

        # Extract invoice-specific fields
        invoice_data = {
            "vendor_name": "",
            "vendor_address": "",
            "customer_name": "",
            "customer_address": "",
            "invoice_date": "",
            "due_date": "",
            "invoice_id": "",
            "total_amount": "",
            "tax_amount": "",
            "items": []
        }

        kv_pairs = result.get("key_value_pairs", {})

        # Map common invoice fields
        field_mappings = {
            "VendorName": "vendor_name",
            "VendorAddress": "vendor_address",
            "CustomerName": "customer_name",
            "CustomerAddress": "customer_address",
            "InvoiceDate": "invoice_date",
            "DueDate": "due_date",
            "InvoiceId": "invoice_id",
            "InvoiceTotal": "total_amount",
            "TotalTax": "tax_amount"
        }

        for key, value in kv_pairs.items():
            for entity_key, field in field_mappings.items():
                if entity_key.lower() in key.lower():
                    invoice_data[field] = value.get("value", "")
                    break

        # Extract line items from tables
        tables = result.get("tables", [])
        if tables:
            # Assume first table is line items
            table = tables[0]
            for cell in table.get("cells", []):
                if cell["row_index"] > 0:  # Skip header row
                    # This is simplified - real implementation would parse columns
                    pass

        return invoice_data

    def extract_receipt_data(self, document_data: bytes) -> Dict[str, Any]:
        """
        Extract data from receipt

        Returns:
            Receipt fields
        """
        result = self.analyze_document(document_data, model="prebuilt-receipt")

        if not result["success"]:
            return {"error": result.get("error", "Receipt analysis failed")}

        receipt_data = {
            "merchant_name": "",
            "transaction_date": "",
            "total": "",
            "tax": "",
            "items": []
        }

        kv_pairs = result.get("key_value_pairs", {})

        # Similar mapping as invoice
        field_mappings = {
            "MerchantName": "merchant_name",
            "TransactionDate": "transaction_date",
            "Total": "total",
            "Tax": "tax"
        }

        for key, value in kv_pairs.items():
            for entity_key, field in field_mappings.items():
                if entity_key.lower() in key.lower():
                    receipt_data[field] = value.get("value", "")
                    break

        return receipt_data

    def classify_document(self, document_data: bytes) -> Dict[str, Any]:
        """
        Classify document type using layout analysis

        Returns:
            {"document_type": "invoice|receipt|contract|other", "confidence": float}
        """
        result = self.analyze_document(document_data, model="prebuilt-layout")

        if not result["success"]:
            return {"document_type": "unknown", "confidence": 0.0}

        # Simple classification based on detected elements
        content = result.get("content", "").lower()
        entities = result.get("entities", [])

        # Check for invoice indicators
        if any("invoice" in content for content in [content]) or \
           any(entity.get("category") == "Invoice" for entity in entities):
            return {"document_type": "invoice", "confidence": 0.8}

        # Check for receipt indicators
        if "receipt" in content or "total" in content:
            return {"document_type": "receipt", "confidence": 0.7}

        # Check for contract indicators
        if "agreement" in content or "contract" in content:
            return {"document_type": "contract", "confidence": 0.6}

        return {"document_type": "document", "confidence": 0.5}

    def get_supported_models(self) -> List[str]:
        """Get list of supported models"""
        return list(self.models.keys())


# Example usage
if __name__ == "__main__":
    service = DocumentIntelligenceService()

    # Test with dummy data (would need real PDF/image bytes)
    print(f"Supported models: {service.get_supported_models()}")

    # In real usage:
    # with open("invoice.pdf", "rb") as f:
    #     data = f.read()
    #     result = service.extract_invoice_data(data)
    #     print(result)