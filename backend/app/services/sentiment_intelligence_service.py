"""
Cross-Language Sentiment Intelligence Service
Multi-language sentiment analysis using Azure AI Language
"""

from typing import Dict, List, Any, Optional
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import os
from openai import AzureOpenAI
import json

class SentimentIntelligenceService:
    """
    Cross-language sentiment analysis and intelligence
    """

    def __init__(self):
        self.endpoint = os.getenv("AZURE_AI_LANGUAGE_ENDPOINT")
        self.key = os.getenv("AZURE_AI_LANGUAGE_KEY")

        if self.key:
            credential = AzureKeyCredential(self.key)
        else:
            credential = DefaultAzureCredential()

        self.client = TextAnalyticsClient(
            endpoint=self.endpoint,
            credential=credential
        )

        # Azure OpenAI for advanced analysis
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2023-12-01-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

        self.chat_model = os.getenv("AZURE_OPENAI_CHAT_MODEL", "gpt-4")

        # Supported languages for sentiment analysis
        self.supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko", "ar", "hi", "ru"
        ]

    def analyze_sentiment(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Analyze sentiment of text

        Args:
            text: Text to analyze
            language: Language code (e.g., 'en', 'es', 'fr')

        Returns:
            Sentiment analysis results
        """
        if not text or len(text.strip()) == 0:
            return {
                "sentiment": "neutral",
                "confidence_scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                "error": "Empty text provided"
            }

        try:
            # Use Azure AI Language for basic sentiment
            response = self.client.analyze_sentiment(
                documents=[text],
                language=language
            )

            result = response[0]

            if result.is_error:
                return {
                    "sentiment": "neutral",
                    "confidence_scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                    "error": result.error.message
                }

            sentiment_result = {
                "sentiment": result.sentiment,
                "confidence_scores": {
                    "positive": result.confidence_scores.positive,
                    "neutral": result.confidence_scores.neutral,
                    "negative": result.confidence_scores.negative
                },
                "sentences": []
            }

            # Add sentence-level analysis
            if result.sentences:
                for sentence in result.sentences:
                    sentiment_result["sentences"].append({
                        "text": sentence.text,
                        "sentiment": sentence.sentiment,
                        "confidence_scores": {
                            "positive": sentence.confidence_scores.positive,
                            "neutral": sentence.confidence_scores.neutral,
                            "negative": sentence.confidence_scores.negative
                        },
                        "offset": sentence.offset,
                        "length": sentence.length
                    })

            return sentiment_result

        except Exception as e:
            # Fallback to neutral if service fails
            return {
                "sentiment": "neutral",
                "confidence_scores": {"positive": 0.0, "neutral": 1.0, "negative": 0.0},
                "error": str(e)
            }

    def analyze_batch_sentiment(self, texts: List[str], languages: List[str] = None) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple texts

        Args:
            texts: List of texts to analyze
            languages: List of language codes (optional)

        Returns:
            List of sentiment results
        """
        if not languages:
            languages = ["en"] * len(texts)

        results = []
        for text, lang in zip(texts, languages):
            result = self.analyze_sentiment(text, lang)
            results.append(result)

        return results

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect language of text

        Args:
            text: Text to analyze

        Returns:
            Language detection result
        """
        try:
            response = self.client.detect_language(documents=[text])
            result = response[0]

            if result.is_error:
                return {"language": "unknown", "confidence": 0.0, "error": result.error.message}

            return {
                "language": result.primary_language.iso6391_name,
                "confidence": result.primary_language.confidence_score,
                "name": result.primary_language.name
            }

        except Exception as e:
            return {"language": "unknown", "confidence": 0.0, "error": str(e)}

    def analyze_emotion(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Advanced emotion analysis using Azure OpenAI

        Args:
            text: Text to analyze
            language: Language code

        Returns:
            Emotion analysis with intensity scores
        """
        try:
            system_prompt = """Analyze the emotions in the following text. Return a JSON object with emotion scores from 0.0 to 1.0 for: joy, sadness, anger, fear, surprise, disgust, anticipation, trust, love.

Format: {"joy": 0.0, "sadness": 0.0, "anger": 0.0, "fear": 0.0, "surprise": 0.0, "disgust": 0.0, "anticipation": 0.0, "trust": 0.0, "love": 0.0}"""

            response = self.openai_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Text: {text}"}
                ],
                max_tokens=200,
                temperature=0.3
            )

            emotion_scores = json.loads(response.choices[0].message.content)

            # Determine dominant emotion
            dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])

            return {
                "emotions": emotion_scores,
                "dominant_emotion": dominant_emotion[0],
                "dominant_score": dominant_emotion[1],
                "emotion_intensity": sum(emotion_scores.values())
            }

        except Exception as e:
            return {
                "emotions": {},
                "dominant_emotion": "unknown",
                "dominant_score": 0.0,
                "emotion_intensity": 0.0,
                "error": str(e)
            }

    def analyze_sentiment_trends(self, texts: List[str], languages: List[str] = None) -> Dict[str, Any]:
        """
        Analyze sentiment trends across multiple texts

        Args:
            texts: List of texts
            languages: List of language codes

        Returns:
            Trend analysis
        """
        if not languages:
            languages = ["en"] * len(texts)

        sentiments = self.analyze_batch_sentiment(texts, languages)

        # Aggregate sentiment scores
        total_positive = sum(s.get("confidence_scores", {}).get("positive", 0) for s in sentiments)
        total_neutral = sum(s.get("confidence_scores", {}).get("neutral", 0) for s in sentiments)
        total_negative = sum(s.get("confidence_scores", {}).get("negative", 0) for s in sentiments)

        count = len(sentiments)
        avg_positive = total_positive / count if count > 0 else 0
        avg_neutral = total_neutral / count if count > 0 else 0
        avg_negative = total_negative / count if count > 0 else 0

        # Determine overall sentiment
        if avg_positive > avg_negative and avg_positive > avg_neutral:
            overall_sentiment = "positive"
        elif avg_negative > avg_positive and avg_negative > avg_neutral:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        # Sentiment distribution
        sentiment_counts = {
            "positive": sum(1 for s in sentiments if s.get("sentiment") == "positive"),
            "neutral": sum(1 for s in sentiments if s.get("sentiment") == "neutral"),
            "negative": sum(1 for s in sentiments if s.get("sentiment") == "negative")
        }

        return {
            "overall_sentiment": overall_sentiment,
            "average_scores": {
                "positive": avg_positive,
                "neutral": avg_neutral,
                "negative": avg_negative
            },
            "sentiment_distribution": sentiment_counts,
            "total_texts": count,
            "sentiment_ratio": {
                "positive": sentiment_counts["positive"] / count if count > 0 else 0,
                "neutral": sentiment_counts["neutral"] / count if count > 0 else 0,
                "negative": sentiment_counts["negative"] / count if count > 0 else 0
            }
        }

    def extract_opinions(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Extract opinions and aspects from text

        Args:
            text: Text to analyze
            language: Language code

        Returns:
            Opinion mining results
        """
        try:
            # Use Azure OpenAI for opinion extraction
            system_prompt = """Extract opinions, aspects, and sentiments from the text. Return a JSON object with:
- "aspects": list of aspects mentioned
- "opinions": list of opinions expressed
- "aspect_sentiments": object mapping aspects to sentiment scores

Format: {"aspects": ["aspect1", "aspect2"], "opinions": ["opinion1", "opinion2"], "aspect_sentiments": {"aspect1": "positive"}}"""

            response = self.openai_client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Text: {text}"}
                ],
                max_tokens=300,
                temperature=0.3
            )

            opinion_data = json.loads(response.choices[0].message.content)

            return {
                "aspects": opinion_data.get("aspects", []),
                "opinions": opinion_data.get("opinions", []),
                "aspect_sentiments": opinion_data.get("aspect_sentiments", {}),
                "text_length": len(text)
            }

        except Exception as e:
            return {
                "aspects": [],
                "opinions": [],
                "aspect_sentiments": {},
                "error": str(e)
            }

    def multilingual_sentiment_summary(self, texts_by_language: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Generate sentiment summary across multiple languages

        Args:
            texts_by_language: Dict mapping language codes to lists of texts

        Returns:
            Multilingual sentiment summary
        """
        summary = {}

        for language, texts in texts_by_language.items():
            if texts:
                trends = self.analyze_sentiment_trends(texts, [language] * len(texts))
                summary[language] = {
                    "overall_sentiment": trends["overall_sentiment"],
                    "average_positive": trends["average_scores"]["positive"],
                    "text_count": len(texts),
                    "sentiment_distribution": trends["sentiment_distribution"]
                }

        # Cross-language comparison
        if len(summary) > 1:
            avg_sentiments = {}
            for lang, data in summary.items():
                if data["overall_sentiment"] == "positive":
                    avg_sentiments[lang] = data["average_positive"]
                elif data["overall_sentiment"] == "negative":
                    avg_sentiments[lang] = -data["average_scores"]["negative"]
                else:
                    avg_sentiments[lang] = 0

            most_positive_lang = max(avg_sentiments.items(), key=lambda x: x[1])
            most_negative_lang = min(avg_sentiments.items(), key=lambda x: x[1])

            summary["cross_language_comparison"] = {
                "most_positive_language": most_positive_lang[0],
                "most_negative_language": most_negative_lang[0],
                "sentiment_variance": max(avg_sentiments.values()) - min(avg_sentiments.values())
            }

        return summary

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()


# Example usage
if __name__ == "__main__":
    sentiment_service = SentimentIntelligenceService()

    # Test sentiment analysis
    test_texts = [
        "I love this product! It's amazing and works perfectly.",
        "This is okay, nothing special.",
        "I hate this, it doesn't work at all and is terrible.",
        "Me encanta este producto, es increíble.",
        "C'est un produit moyen, rien d'exceptionnel."
    ]

    languages = ["en", "en", "en", "es", "fr"]

    results = sentiment_service.analyze_batch_sentiment(test_texts, languages)

    for i, result in enumerate(results):
        print(f"Text {i+1}: {result['sentiment']} (pos: {result['confidence_scores']['positive']:.2f})")

    # Test trends
    trends = sentiment_service.analyze_sentiment_trends(test_texts, languages)
    print(f"\nOverall trend: {trends['overall_sentiment']}")
    print(f"Distribution: {trends['sentiment_distribution']}")