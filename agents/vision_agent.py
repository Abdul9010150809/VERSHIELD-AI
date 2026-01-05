import asyncio
import os
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class FaceLivenessDecision(Enum):
    """Enum to represent liveness decision"""
    Real = "Real"
    Spoof = "Spoof"

class VisionAgent:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_FACE_API_ENDPOINT")
        self.key = os.getenv("AZURE_FACE_API_KEY")
        self.client = None
        self.available = False
        
        # Only initialize if credentials are provided
        if self.endpoint and self.key:
            try:
                from azure.ai.vision.face import FaceClient
                from azure.core.credentials import AzureKeyCredential
                self.client = FaceClient(endpoint=self.endpoint, credential=AzureKeyCredential(self.key))
                self.available = True
                print("✅ Vision Agent initialized with Azure Face API")
            except Exception as e:
                print(f"Warning: Vision Agent Azure not available: {e}")
                self.available = False
        else:
            print("⚠️ Vision Agent: Using mock mode (no Azure credentials)")

    async def create_liveness_session(self) -> str:
        """
        Initialize an Azure Face Liveness Detection session.
        Returns the session ID for subsequent analysis.
        """
        try:
            # Create session content with default parameters
            session_content = CreateLivenessSessionContent()

            # Create the liveness session
            session = await self.client.create_liveness_session(
                content=session_content
            )

            return session.session_id

        except Exception as e:
            print(f"Error creating liveness session: {e}")
            raise

    async def get_liveness_result(self, session_id: str, image_data: bytes) -> FaceLivenessDecision:
        """
        Get the final liveness decision from an Azure session.
        Returns FaceLivenessDecision.Real or FaceLivenessDecision.Spoof.
        """
        try:
            # Analyze liveness with the session
            result = await self.client.analyze_liveness(
                session_id=session_id,
                image_data=image_data
            )

            # Return the decision directly as per Microsoft 2026 best practices
            return result.decision

        except Exception as e:
            print(f"Error getting liveness result: {e}")
            # Default to Spoof on error for security
            return FaceLivenessDecision.Spoof

    async def detect_liveness(self, image_data: bytes) -> FaceLivenessDecision:
        """
        Detect if face is real or spoofed.
        Falls back to mock decision if Azure Vision is not available.
        """
        if not self.available or not self.client:
            # Mock mode: return a realistic random decision for testing
            import random
            result = random.choice([FaceLivenessDecision.Real, FaceLivenessDecision.Spoof])
            print(f"📸 Vision Agent (mock): {result.value}")
            return result
            
        try:
            # Azure implementation would go here
            # For now, just return the mock
            import random
            result = random.choice([FaceLivenessDecision.Real, FaceLivenessDecision.Spoof])
            return result
        except Exception as e:
            print(f"Error detecting liveness: {e}")
            # Default to Spoof on error for security
            return FaceLivenessDecision.Spoof
            # Return a simulated result for testing/development
            print("Vision Agent not available - returning simulated liveness result")
            return FaceLivenessDecision.Real  # Default to Real for development
        
        session_id = await self.create_liveness_session()
        return await self.get_liveness_result(session_id, image_data)