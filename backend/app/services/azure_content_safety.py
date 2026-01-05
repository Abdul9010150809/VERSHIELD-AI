"""
Azure AI Content Safety Shield
Comprehensive content moderation for text, images, and videos
"""
import os
import asyncio
from typing import Dict, List, Optional, Any
from azure.ai.contentsafety.aio import ContentSafetyClient  # type: ignore
from azure.ai.contentsafety.models import (  # type: ignore
    AnalyzeTextOptions,
    AnalyzeImageOptions,
    TextCategory,
    ImageCategory
)
from azure.core.credentials import AzureKeyCredential
import base64

class ContentSafetyShield:
    """
    Azure AI Content Safety integration for multi-modal threat detection
    """
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
        self.key = os.getenv("AZURE_CONTENT_SAFETY_KEY")
        
        if self.endpoint and self.key:
            self.client = ContentSafetyClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
        else:
            self.client = None
            print("Warning: Azure Content Safety credentials not configured")
        
        # Severity thresholds (0-7, higher is more severe)
        self.thresholds = {
            "hate": 2,
            "self_harm": 2,
            "sexual": 2,
            "violence": 2
        }
    
    async def analyze_text(
        self,
        text: str,
        categories: Optional[List[str]] = None,
        blocklist_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze text content for safety issues
        """
        if not self.client:
            return self._get_fallback_response("text")
        
        try:
            # Prepare analysis options
            options = AnalyzeTextOptions(text=text)
            
            if blocklist_names:
                options.blocklist_names = blocklist_names
            
            async with self.client:
                response = await self.client.analyze_text(options)
                
                results = {
                    "safe": True,
                    "categories": {},
                    "blocklist_matches": [],
                    "severity_scores": {}
                }
                
                # Process category analyses
                for category_analysis in response.categories_analysis:
                    category = category_analysis.category
                    severity = category_analysis.severity
                    
                    results["categories"][category] = {
                        "severity": severity,
                        "flagged": severity > self.thresholds.get(category.lower(), 2)
                    }
                    
                    results["severity_scores"][category] = severity
                    
                    if severity > self.thresholds.get(category.lower(), 2):
                        results["safe"] = False
                
                # Process blocklist matches
                if hasattr(response, 'blocklists_match') and response.blocklists_match:
                    for match in response.blocklists_match:
                        results["blocklist_matches"].append({
                            "blocklist_name": match.blocklist_name,
                            "blocklist_item_id": match.blocklist_item_id,
                            "blocklist_item_text": match.blocklist_item_text
                        })
                        results["safe"] = False
                
                return results
                
        except Exception as e:
            print(f"Content safety analysis error: {e}")
            return self._get_fallback_response("text")
    
    async def analyze_image(
        self,
        image_data: bytes,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze image content for safety issues
        """
        if not self.client:
            return self._get_fallback_response("image")
        
        try:
            options = AnalyzeImageOptions(image={"content": image_data})
            
            async with self.client:
                response = await self.client.analyze_image(options)
                
                results = {
                    "safe": True,
                    "categories": {},
                    "severity_scores": {}
                }
                
                for category_analysis in response.categories_analysis:
                    category = category_analysis.category
                    severity = category_analysis.severity
                    
                    results["categories"][category] = {
                        "severity": severity,
                        "flagged": severity > self.thresholds.get(category.lower(), 2)
                    }
                    
                    results["severity_scores"][category] = severity
                    
                    if severity > self.thresholds.get(category.lower(), 2):
                        results["safe"] = False
                
                return results
                
        except Exception as e:
            print(f"Image safety analysis error: {e}")
            return self._get_fallback_response("image")
    
    async def analyze_multimodal(
        self,
        text: Optional[str] = None,
        image_data: Optional[bytes] = None,
        video_frames: Optional[List[bytes]] = None
    ) -> Dict[str, Any]:
        """
        Analyze multiple content types in a single request
        """
        results = {
            "overall_safe": True,
            "text_analysis": None,
            "image_analysis": None,
            "video_analysis": None,
            "threat_score": 0.0
        }
        
        tasks = []
        
        if text:
            tasks.append(("text", self.analyze_text(text)))
        
        if image_data:
            tasks.append(("image", self.analyze_image(image_data)))
        
        if video_frames:
            # Analyze sample frames from video
            sample_frames = video_frames[::max(len(video_frames)//5, 1)][:5]
            tasks.extend([("video_frame", self.analyze_image(frame)) for frame in sample_frames])
        
        # Execute all analyses in parallel
        analysis_results = await asyncio.gather(*[task[1] for task in tasks])
        
        # Process results
        max_severity = 0
        for i, (analysis_type, result) in enumerate(zip([t[0] for t in tasks], analysis_results)):
            if analysis_type == "text":
                results["text_analysis"] = result
                if not result["safe"]:
                    results["overall_safe"] = False
                max_severity = max(max_severity, max(result["severity_scores"].values(), default=0))
            
            elif analysis_type == "image":
                results["image_analysis"] = result
                if not result["safe"]:
                    results["overall_safe"] = False
                max_severity = max(max_severity, max(result["severity_scores"].values(), default=0))
            
            elif analysis_type == "video_frame":
                if results["video_analysis"] is None:
                    results["video_analysis"] = {"frames": [], "safe": True}
                results["video_analysis"]["frames"].append(result)
                if not result["safe"]:
                    results["video_analysis"]["safe"] = False
                    results["overall_safe"] = False
                max_severity = max(max_severity, max(result["severity_scores"].values(), default=0))
        
        # Calculate threat score (0-100)
        results["threat_score"] = min(100, (max_severity / 7) * 100)
        
        return results
    
    async def create_blocklist(
        self,
        blocklist_name: str,
        description: str
    ) -> Dict[str, Any]:
        """
        Create a custom blocklist for organization-specific terms
        """
        if not self.client:
            return {"success": False, "error": "Client not configured"}
        
        try:
            async with self.client:
                response = await self.client.create_or_update_text_blocklist(
                    blocklist_name=blocklist_name,
                    options={"description": description}
                )
                
                return {
                    "success": True,
                    "blocklist_name": response.blocklist_name,
                    "description": response.description
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def add_blocklist_items(
        self,
        blocklist_name: str,
        items: List[str]
    ) -> Dict[str, Any]:
        """
        Add items to a blocklist
        """
        if not self.client:
            return {"success": False, "error": "Client not configured"}
        
        try:
            async with self.client:
                blocklist_items = [{"text": item} for item in items]
                response = await self.client.add_blocklist_items(
                    blocklist_name=blocklist_name,
                    options={"blocklist_items": blocklist_items}
                )
                
                return {
                    "success": True,
                    "items_added": len(response.value)
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_fallback_response(self, content_type: str) -> Dict[str, Any]:
        """
        Fallback response when service is unavailable
        """
        return {
            "safe": True,
            "categories": {},
            "severity_scores": {},
            "fallback": True,
            "message": f"Content safety check unavailable for {content_type}"
        }
    
    async def get_safety_report(
        self,
        analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive safety report from multiple analyses
        """
        total_checks = len(analyses)
        flagged_checks = sum(1 for a in analyses if not a.get("safe", True))
        
        category_summaries = {}
        max_threat = 0
        
        for analysis in analyses:
            for category, data in analysis.get("categories", {}).items():
                if category not in category_summaries:
                    category_summaries[category] = {
                        "total_occurrences": 0,
                        "max_severity": 0,
                        "flagged_count": 0
                    }
                
                category_summaries[category]["total_occurrences"] += 1
                category_summaries[category]["max_severity"] = max(
                    category_summaries[category]["max_severity"],
                    data.get("severity", 0)
                )
                if data.get("flagged", False):
                    category_summaries[category]["flagged_count"] += 1
                
                max_threat = max(max_threat, data.get("severity", 0))
        
        risk_level = "low"
        if max_threat >= 4:
            risk_level = "high"
        elif max_threat >= 2:
            risk_level = "medium"
        
        return {
            "total_checks": total_checks,
            "flagged_checks": flagged_checks,
            "pass_rate": ((total_checks - flagged_checks) / total_checks * 100) if total_checks > 0 else 100,
            "category_summaries": category_summaries,
            "risk_level": risk_level,
            "max_threat_score": max_threat,
            "recommendation": self._get_recommendation(risk_level, category_summaries)
        }
    
    def _get_recommendation(
        self,
        risk_level: str,
        categories: Dict[str, Any]
    ) -> str:
        """
        Generate recommendation based on safety analysis
        """
        if risk_level == "high":
            return "BLOCK: Content contains high-severity violations and should be blocked"
        elif risk_level == "medium":
            return "REVIEW: Content requires manual review before approval"
        else:
            return "ALLOW: Content passed safety checks"
    
    async def close(self):
        """Close the client connection"""
        if self.client:
            await self.client.close()
