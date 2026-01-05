import asyncio
import hashlib
import numpy as np
from typing import Dict, Any
import aiohttp
import time
from azure.core.exceptions import AzureError
from .visual_agent.face_liveness import FaceLivenessDetector
from .visual_agent.pixel_artifact_analysis import PixelArtifactAnalyzer
from .acoustic_agent.frequency_analysis import FrequencyAnomalyDetector
from .reasoning_agent.risk_correlation import RiskCorrelator
from ..config.settings import Config

class AzureOrchestrator:
    def __init__(self):
        self.config = Config()
        self.face_detector = FaceLivenessDetector(self.config)
        self.pixel_analyzer = PixelArtifactAnalyzer(self.config)
        self.frequency_detector = FrequencyAnomalyDetector(self.config)
        self.risk_correlator = RiskCorrelator(self.config)
        self.session = aiohttp.ClientSession()

    async def process_media(self, video_data: bytes, audio_data: bytes) -> Dict[str, Any]:
        """
        Process video and audio data for deepfake detection.
        Converts media to hashes/vectors immediately for privacy.
        """
        start_time = time.time()

        # Convert to hashes/vectors immediately
        video_hash = self._hash_media(video_data)
        audio_hash = self._hash_media(audio_data)

        # Extract features (vectors)
        video_vector = self._extract_video_vector(video_data)
        audio_vector = self._extract_audio_vector(audio_data)

        # Run agents concurrently
        visual_task = self._run_visual_analysis(video_vector)
        acoustic_task = self._run_acoustic_analysis(audio_vector)
        reasoning_task = self._run_reasoning_analysis()

        results = await asyncio.gather(visual_task, acoustic_task, reasoning_task, return_exceptions=True)

        visual_risk, acoustic_risk, combined_risk = results

        # Check latency
        latency = time.time() - start_time
        if latency > 1.2:
            print(f"Warning: Latency exceeded 1.2s: {latency}")

        # Trigger soft lock if risk > 85%
        if combined_risk > 85:
            await self._trigger_soft_lock(combined_risk)

        return {
            "visual_risk": visual_risk,
            "acoustic_risk": acoustic_risk,
            "combined_risk": combined_risk,
            "latency": latency,
            "video_hash": video_hash,
            "audio_hash": audio_hash
        }

    def _hash_media(self, data: bytes) -> str:
        """Generate SHA-256 hash of media data."""
        return hashlib.sha256(data).hexdigest()

    def _extract_video_vector(self, video_data: bytes) -> np.ndarray:
        """Extract feature vector from video (placeholder)."""
        # In real implementation, use OpenCV or similar to extract features
        return np.random.rand(512)  # Placeholder

    def _extract_audio_vector(self, audio_data: bytes) -> np.ndarray:
        """Extract feature vector from audio (placeholder)."""
        # In real implementation, use librosa or similar
        return np.random.rand(256)  # Placeholder

    async def _run_visual_analysis(self, video_vector: np.ndarray) -> float:
        """Run visual agents and return risk score."""
        try:
            liveness_score = await self.face_detector.detect_liveness(video_vector)
            artifact_score = await self.pixel_analyzer.analyze_artifacts(video_vector)
            return (liveness_score + artifact_score) / 2
        except AzureError as e:
            print(f"Visual analysis error: {e}")
            return 50.0  # Default risk

    async def _run_acoustic_analysis(self, audio_vector: np.ndarray) -> float:
        """Run acoustic agent and return risk score."""
        try:
            return await self.frequency_detector.detect_anomalies(audio_vector)
        except AzureError as e:
            print(f"Acoustic analysis error: {e}")
            return 50.0

    async def _run_reasoning_analysis(self) -> float:
        """Run reasoning agent to correlate risks."""
        try:
            # This would take inputs from visual and acoustic, but for simplicity
            return await self.risk_correlator.correlate_risks(50.0, 50.0)  # Placeholder
        except AzureError as e:
            print(f"Reasoning analysis error: {e}")
            return 50.0

    async def _trigger_soft_lock(self, risk_score: float):
        """Trigger Azure Function for soft lock."""
        try:
            async with self.session.post(
                self.config.AZURE_FUNCTION_URL,
                json={"risk_score": risk_score, "action": "soft_lock"}
            ) as response:
                if response.status == 200:
                    print("Soft lock triggered successfully")
                else:
                    print(f"Failed to trigger soft lock: {response.status}")
        except Exception as e:
            print(f"Error triggering soft lock: {e}")

    async def close(self):
        """Close the session."""
        await self.session.close()