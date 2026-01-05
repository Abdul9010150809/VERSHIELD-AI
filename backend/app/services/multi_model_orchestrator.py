"""
Multi-Model Intelligence Orchestration Service
Coordinates multiple AI models for comprehensive analysis
"""

import asyncio
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import time

from .pii_redaction_service import PIIRedactionService
from .content_safety_shield import ContentSafetyShield
from .semantic_cache_service import SemanticCacheService
from .vector_rag_service import VectorRAGService

class MultiModelOrchestrator:
    """
    Orchestrates multiple AI models for intelligent content processing
    """

    def __init__(self):
        self.pii_service = PIIRedactionService()
        self.safety_shield = ContentSafetyShield()
        self.cache_service = SemanticCacheService()
        self.rag_service = VectorRAGService()

        self.executor = ThreadPoolExecutor(max_workers=4)

    async def process_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content through multiple AI models

        Args:
            content: Dict with 'text', 'images', 'documents', etc.

        Returns:
            Comprehensive analysis results
        """
        start_time = time.time()

        text = content.get("text", "")
        images = content.get("images", [])
        documents = content.get("documents", [])

        # Run all analyses concurrently
        tasks = []

        if text:
            tasks.extend([
                self._analyze_text_safety(text),
                self._redact_pii(text),
                self._check_cache(text),
                self._rag_query(text)
            ])

        if images:
            tasks.extend([self._analyze_image_safety(img) for img in images])

        if documents:
            tasks.extend([self._extract_document_intelligence(doc) for doc in documents])

        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        analysis_results = {
            "text_analysis": {},
            "image_analysis": [],
            "document_analysis": [],
            "performance": {},
            "recommendations": []
        }

        result_idx = 0

        # Text safety
        if text:
            try:
                analysis_results["text_analysis"]["safety"] = results[result_idx]
                result_idx += 1
            except:
                analysis_results["text_analysis"]["safety"] = {"error": "Safety analysis failed"}

        # PII Redaction
        if text:
            try:
                analysis_results["text_analysis"]["pii_redaction"] = results[result_idx]
                result_idx += 1
            except:
                analysis_results["text_analysis"]["pii_redaction"] = {"error": "PII redaction failed"}

        # Cache check
        if text:
            try:
                analysis_results["text_analysis"]["cache_hit"] = results[result_idx]
                result_idx += 1
            except:
                analysis_results["text_analysis"]["cache_hit"] = None

        # RAG query
        if text:
            try:
                analysis_results["text_analysis"]["rag_response"] = results[result_idx]
                result_idx += 1
            except:
                analysis_results["text_analysis"]["rag_response"] = {"error": "RAG query failed"}

        # Image analysis
        for i, img in enumerate(images):
            try:
                analysis_results["image_analysis"].append(results[result_idx])
                result_idx += 1
            except:
                analysis_results["image_analysis"].append({"error": "Image analysis failed"})

        # Document analysis
        for i, doc in enumerate(documents):
            try:
                analysis_results["document_analysis"].append(results[result_idx])
                result_idx += 1
            except:
                analysis_results["document_analysis"].append({"error": "Document analysis failed"})

        # Performance metrics
        processing_time = time.time() - start_time
        analysis_results["performance"] = {
            "total_time": processing_time,
            "models_used": len(tasks),
            "throughput": len(tasks) / processing_time if processing_time > 0 else 0
        }

        # Generate recommendations
        analysis_results["recommendations"] = self._generate_recommendations(analysis_results)

        return analysis_results

    async def _analyze_text_safety(self, text: str) -> Dict[str, Any]:
        """Analyze text safety"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.safety_shield.analyze_text, text)

    async def _redact_pii(self, text: str) -> Dict[str, Any]:
        """Redact PII from text"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.pii_service.redact_text, text)

    async def _check_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """Check semantic cache"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.cache_service.get_cached_response, query)

    async def _rag_query(self, query: str) -> Dict[str, Any]:
        """Perform RAG query"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.rag_service.rag_query, query)

    async def _analyze_image_safety(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze image safety"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.safety_shield.analyze_image, image_data)

    async def _extract_document_intelligence(self, document_data: bytes) -> Dict[str, Any]:
        """Extract intelligence from document (placeholder)"""
        # This would integrate with Azure Document Intelligence
        # For now, return placeholder
        return {
            "extracted_text": "Document processing not implemented yet",
            "entities": [],
            "key_value_pairs": {},
            "tables": []
        }

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        text_analysis = results.get("text_analysis", {})

        # Safety recommendations
        safety = text_analysis.get("safety", {})
        if not safety.get("is_safe", True):
            recommendations.append("Content flagged for safety violations - review before processing")

        # PII recommendations
        pii = text_analysis.get("pii_redaction", {})
        if pii.get("redaction_count", 0) > 0:
            recommendations.append(f"Redacted {pii['redaction_count']} PII entities")

        # Cache recommendations
        cache_hit = text_analysis.get("cache_hit")
        if cache_hit:
            recommendations.append("Response served from semantic cache for efficiency")

        # Performance recommendations
        perf = results.get("performance", {})
        if perf.get("total_time", 0) > 5.0:
            recommendations.append("Processing time exceeded 5 seconds - consider optimization")

        return recommendations

    async def batch_process(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple contents in batch

        Args:
            contents: List of content dicts

        Returns:
            List of analysis results
        """
        tasks = [self.process_content(content) for content in contents]
        return await asyncio.gather(*tasks)

    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            "services": {
                "pii_redaction": "active",
                "content_safety": "active",
                "semantic_cache": self.cache_service.get_cache_stats(),
                "vector_rag": self.rag_service.get_index_stats()
            },
            "executor": {
                "max_workers": self.executor._max_workers,
                "active_threads": len(self.executor._threads)
            }
        }

    async def close(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)


# Example usage
if __name__ == "__main__":
    async def main():
        orchestrator = MultiModelOrchestrator()

        test_content = {
            "text": "Hello, my name is John Doe and my SSN is 123-45-6789. I work at Microsoft.",
            "images": [],
            "documents": []
        }

        result = await orchestrator.process_content(test_content)
        print(f"Analysis completed in {result['performance']['total_time']:.2f}s")
        print(f"Recommendations: {result['recommendations']}")

        await orchestrator.close()

    asyncio.run(main())