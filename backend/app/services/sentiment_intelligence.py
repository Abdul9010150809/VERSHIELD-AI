"""
Cross-Language Sentiment Intelligence
Multi-language sentiment analysis using Azure AI Language
"""
import os
from typing import Dict, List, Optional, Any
from azure.ai.textanalytics.aio import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

class SentimentIntelligence:
    """
    Advanced sentiment analysis across multiple languages
    """
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_LANGUAGE_ENDPOINT")
        self.key = os.getenv("AZURE_LANGUAGE_KEY")
        
        if self.endpoint and self.key:
            self.client = TextAnalyticsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.key)
            )
        else:
            self.client = None
            print("Warning: Azure Language credentials not configured")
    
    async def analyze_sentiment(
        self,
        text: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment with detailed confidence scores
        """
        if not self.client:
            return self._get_fallback_sentiment()
        
        try:
            async with self.client:
                documents = [text]
                response = await self.client.analyze_sentiment(
                    documents=documents,
                    language=language,
                    show_opinion_mining=True
                )
                
                result = response[0]
                
                if result.is_error:
                    return {"error": result.error.message}
                
                return {
                    "sentiment": result.sentiment,
                    "confidence_scores": {
                        "positive": result.confidence_scores.positive,
                        "neutral": result.confidence_scores.neutral,
                        "negative": result.confidence_scores.negative
                    },
                    "sentences": [
                        {
                            "text": sentence.text,
                            "sentiment": sentence.sentiment,
                            "confidence_scores": {
                                "positive": sentence.confidence_scores.positive,
                                "neutral": sentence.confidence_scores.neutral,
                                "negative": sentence.confidence_scores.negative
                            },
                            "opinions": [
                                {
                                    "target": opinion.target.text,
                                    "sentiment": opinion.target.sentiment,
                                    "assessments": [
                                        {
                                            "text": assessment.text,
                                            "sentiment": assessment.sentiment
                                        }
                                        for assessment in opinion.assessments
                                    ]
                                }
                                for opinion in sentence.mined_opinions
                            ] if hasattr(sentence, 'mined_opinions') else []
                        }
                        for sentence in result.sentences
                    ],
                    "language": result.language if hasattr(result, 'language') else language
                }
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return self._get_fallback_sentiment()
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect text language"""
        if not self.client:
            return {"language": "en", "confidence": 0.5}
        
        try:
            async with self.client:
                response = await self.client.detect_language(documents=[text])
                result = response[0]
                
                return {
                    "language": result.primary_language.iso6391_name,
                    "confidence": result.primary_language.confidence_score
                }
        except Exception as e:
            print(f"Language detection error: {e}")
            return {"language": "en", "confidence": 0.5}
    
    async def analyze_key_phrases(
        self,
        text: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract key phrases"""
        if not self.client:
            return {"key_phrases": []}
        
        try:
            async with self.client:
                response = await self.client.extract_key_phrases(
                    documents=[text],
                    language=language
                )
                
                result = response[0]
                return {
                    "key_phrases": result.key_phrases,
                    "language": language
                }
        except Exception as e:
            print(f"Key phrase extraction error: {e}")
            return {"key_phrases": []}
    
    async def comprehensive_analysis(
        self,
        text: str
    ) -> Dict[str, Any]:
        """
        Perform comprehensive text analysis
        """
        # Detect language first
        lang_result = await self.detect_language(text)
        language = lang_result["language"]
        
        # Run analyses in parallel
        import asyncio
        sentiment_task = self.analyze_sentiment(text, language)
        phrases_task = self.analyze_key_phrases(text, language)
        
        sentiment, phrases = await asyncio.gather(sentiment_task, phrases_task)
        
        return {
            "language": language,
            "language_confidence": lang_result["confidence"],
            "sentiment": sentiment,
            "key_phrases": phrases["key_phrases"],
            "text_length": len(text)
        }
    
    def _get_fallback_sentiment(self) -> Dict[str, Any]:
        """Fallback sentiment response"""
        return {
            "sentiment": "neutral",
            "confidence_scores": {
                "positive": 0.33,
                "neutral": 0.34,
                "negative": 0.33
            },
            "sentences": [],
            "fallback": True
        }
    
    async def close(self):
        """Close client"""
        if self.client:
            await self.client.close()
