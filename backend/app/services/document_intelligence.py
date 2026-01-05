"""
Azure Document Intelligence Service
Automated form and document extraction
"""
import os
from typing import Dict, List, Optional, Any
from azure.ai.formrecognizer.aio import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import asyncio

class DocumentIntelligenceService:
    """
    Azure Document Intelligence for automated document processing
    """
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        if self.endpoint and self.key:
            self.client = DocumentAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
        else:
            self.client = None
            print("Warning: Document Intelligence credentials not configured")
    
    async def analyze_document(
        self,
        document_bytes: bytes,
        model_id: str = "prebuilt-document"
    ) -> Dict[str, Any]:
        """
        Analyze document using specified model
        """
        if not self.client:
            return {"success": False, "error": "Client not configured"}
        
        try:
            async with self.client:
                poller = await self.client.begin_analyze_document(
                    model_id=model_id,
                    document=document_bytes
                )
                result = await poller.result()
                
                return {
                    "success": True,
                    "content": result.content,
                    "pages": len(result.pages),
                    "tables": [self._extract_table(table) for table in result.tables],
                    "key_value_pairs": [
                        {"key": kv.key.content, "value": kv.value.content if kv.value else None}
                        for kv in result.key_value_pairs
                    ],
                    "entities": [
                        {"type": entity.category, "value": entity.content, "confidence": entity.confidence}
                        for entity in result.entities
                    ] if hasattr(result, 'entities') else []
                }
        except Exception as e:
            print(f"Document analysis error: {e}")
            return {"success": False, "error": str(e)}
    
    async def analyze_invoice(self, document_bytes: bytes) -> Dict[str, Any]:
        """Extract invoice data"""
        return await self.analyze_document(document_bytes, "prebuilt-invoice")
    
    async def analyze_receipt(self, document_bytes: bytes) -> Dict[str, Any]:
        """Extract receipt data"""
        return await self.analyze_document(document_bytes, "prebuilt-receipt")
    
    async def analyze_id_document(self, document_bytes: bytes) -> Dict[str, Any]:
        """Extract ID document data"""
        return await self.analyze_document(document_bytes, "prebuilt-idDocument")
    
    def _extract_table(self, table) -> Dict[str, Any]:
        """Extract table data"""
        return {
            "row_count": table.row_count,
            "column_count": table.column_count,
            "cells": [
                {
                    "content": cell.content,
                    "row_index": cell.row_index,
                    "column_index": cell.column_index
                }
                for cell in table.cells
            ]
        }
    
    async def close(self):
        """Close client"""
        if self.client:
            await self.client.close()
