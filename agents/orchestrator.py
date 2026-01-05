import asyncio
import os
import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv
from .vision_agent import VisionAgent
from .acoustic_agent import AcousticAgent
from .pii_redaction_agent import PIIRedactionAgent
from saas.tenant_manager import tenant_manager

load_dotenv()

class Orchestrator:
    def __init__(self):
        self.vision_agent = VisionAgent()
        self.acoustic_agent = AcousticAgent()
        self.pii_agent = PIIRedactionAgent()
        
        # Try Azure OpenAI first, fall back to regular OpenAI
        azure_key = os.getenv("AZURE_OPENAI_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if azure_key and azure_endpoint:
            try:
                self.openai_client = AzureOpenAI(
                    api_key=azure_key,
                    api_version="2023-12-01-preview",
                    azure_endpoint=azure_endpoint
                )
                self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
                self.use_azure = True
            except Exception as e:
                print(f"Warning: Azure OpenAI initialization failed: {e}. Falling back to regular OpenAI.")
                self._init_regular_openai()
        else:
            self._init_regular_openai()
    
    def _init_regular_openai(self):
        """Initialize regular OpenAI client"""
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Skip test/placeholder keys
        if not api_key or api_key.startswith("sk-proj-test"):
            print("⚠️ Orchestrator: No valid OpenAI API key - running in mock mode")
            self.openai_client = None
            self.deployment = "gpt-3.5-turbo"
            self.use_azure = False
            return
            
        self.openai_client = OpenAI(api_key=api_key)
        self.deployment = "gpt-3.5-turbo"
        self.use_azure = False

    @staticmethod
    def anonymize_stream(metadata: dict) -> dict:
        """
        Strip PII from metadata before logging.
        Removes emails, phone numbers, names, etc.
        """
        anonymized = metadata.copy()

        # Remove common PII fields
        pii_fields = ['email', 'phone', 'name', 'first_name', 'last_name', 'address', 'ssn', 'account_number']
        for field in pii_fields:
            if field in anonymized:
                anonymized[field] = "[REDACTED]"

        # Anonymize any string values that look like emails or phones
        for key, value in anonymized.items():
            if isinstance(value, str):
                # Remove emails
                anonymized[key] = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', value)
                # Remove phone numbers (simple pattern)
                anonymized[key] = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', anonymized[key])

        return anonymized

    async def evaluate_transaction(self, image_data: bytes, audio_data: bytes, transaction_amount: float, metadata: dict = None) -> dict:
        """
        Evaluate transaction for deepfake risk.
        Returns dict with decision and reasoning.
        """
        # Run agents concurrently
        vision_decision, acoustic_score = await asyncio.gather(
            self.vision_agent.detect_liveness(image_data),
            self.acoustic_agent.analyze_audio_stream(audio_data)
        )

        # Convert vision decision to score
        vision_score = 0.0 if vision_decision.name == "Real" else 1.0

        # Prepare system prompt for Zero-Trust logic
        system_prompt = """
        You are a Zero-Trust security AI for financial transactions. Assume all inputs could be compromised.
        Based on liveness and acoustic scores, decide to BLOCK or ALLOW the transaction.
        - BLOCK if any score > 0.5 or if there's any suspicion of deepfake.
        - ALLOW only if both scores are < 0.3 and no anomalies detected.
        Provide decision (BLOCK or ALLOW) and brief reasoning.
        """

        user_prompt = f"""
        Transaction amount: ${transaction_amount}
        Vision Liveness Score: {vision_score} (0 = real, 1 = spoof)
        Acoustic Score: {acoustic_score} (0 = natural, 1 = synthetic)
        Metadata: {metadata or {}}
        """

        # Call Azure OpenAI
        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=150
        )

        reasoning = response.choices[0].message.content.strip()
        decision = "BLOCK" if "BLOCK" in reasoning.upper() else "ALLOW"

        return {
            "decision": decision,
            "reasoning": reasoning,
            "vision_score": vision_score,
            "acoustic_score": acoustic_score,
            "transaction_amount": transaction_amount
        }

    async def evaluate_risk(self, vision_result: str, audio_score: float, transaction_value: float, tenant_id: str = None) -> dict:
        """
        Evaluate risk using GPT-4o as a Cyber-Forensics Expert.
        Analyzes multi-modal data to recommend BLOCK or ALLOW.

        Args:
            vision_result: "Real" or "Spoof" from face liveness detection
            audio_score: Risk score from acoustic analysis (0.0-1.0)
            transaction_value: Dollar amount of the transaction
            tenant_id: Tenant identifier for contextual analysis

        Returns:
            dict with decision and reasoning
        """
        try:
            # Get tenant context
            current_tenant = tenant_id or tenant_manager.get_tenant()

            system_prompt = f"""
            You are a Cyber-Forensics Expert specializing in deepfake detection and financial fraud prevention for {current_tenant or 'enterprise'} environments.
            Analyze the provided multi-modal biometric data and transaction details.
            Consider that face liveness detection provides binary Real/Spoof results,
            while acoustic analysis provides a risk score where higher values indicate greater likelihood of AI-generated voice.

            Key principles:
            - If face is "Spoof", always BLOCK regardless of other factors
            - If face is "Real" but voice shows high synthetic risk (>0.7), BLOCK for high-value transactions
            - Consider transaction value: higher amounts warrant stricter scrutiny
            - Prioritize security over convenience
            - Account for tenant-specific risk tolerance and industry context

            Provide a clear BLOCK or ALLOW decision with detailed forensic reasoning.
            """

            user_prompt = f"""
            Transaction Analysis Request for Tenant: {current_tenant or 'Unknown'}

            Face Liveness Result: {vision_result}
            Voice Synthetic Risk Score: {audio_score:.2f} (0.0 = natural, 1.0 = synthetic)
            Transaction Value: ${transaction_value:,.2f}

            Forensic Analysis:
            - Face detection indicates {'authentic human presence' if vision_result == 'Real' else 'potential spoofing attempt'}
            - Voice analysis shows {audio_score:.0%} likelihood of being AI-generated
            - Transaction represents {'high' if transaction_value > 10000 else 'moderate' if transaction_value > 1000 else 'low'} financial risk
            - Tenant context: {current_tenant or 'Standard enterprise security profile'}

            Decision: Should this transaction be BLOCKED or ALLOWED?
            """

            # If no OpenAI client, use fallback logic immediately
            if not self.openai_client:
                print("⚠️ No OpenAI client - using fallback decision logic")
                if vision_result == "Spoof":
                    decision = "BLOCK"
                    reasoning = "Face liveness check failed - spoofing detected. Transaction blocked. (Fallback mode)"
                elif audio_score > 0.7:
                    decision = "BLOCK"
                    reasoning = f"High voice synthesis risk ({audio_score:.0%}). Possible voice cloning detected. (Fallback mode)"
                elif transaction_value > 10000:
                    decision = "BLOCK"
                    reasoning = f"High-value transaction (${transaction_value:,.2f}) with voice risk score {audio_score:.0%}. Blocked for security. (Fallback mode)"
                else:
                    decision = "ALLOW"
                    reasoning = f"Face liveness verified, voice analysis shows {audio_score:.0%} risk. Transaction appears legitimate. (Fallback mode)"
            else:
                try:
                    response = await asyncio.to_thread(
                        self.openai_client.chat.completions.create,
                        model=self.deployment,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=300,
                        temperature=0.1  # Low temperature for consistent security decisions
                    )

                    reasoning = response.choices[0].message.content.strip()
                    decision = "BLOCK" if "BLOCK" in reasoning.upper() else "ALLOW"
                    
                except Exception as api_error:
                    print(f"OpenAI API error (using fallback): {str(api_error)[:100]}")
                    # Fallback logic when API is unavailable
                    if vision_result == "Spoof":
                        decision = "BLOCK"
                        reasoning = "Face liveness check failed - spoofing detected. Transaction blocked."
                    elif audio_score > 0.7:
                        decision = "BLOCK"
                        reasoning = f"High voice synthesis risk ({audio_score:.0%}). Possible voice cloning detected."
                    elif transaction_value > 10000:
                        decision = "BLOCK"
                        reasoning = f"High-value transaction (${transaction_value:,.2f}) with voice risk score {audio_score:.0%}. Blocked for security."
                    else:
                        decision = "ALLOW"
                        reasoning = f"Face liveness verified, voice analysis shows {audio_score:.0%} risk. Transaction appears legitimate."

            return {
                "decision": decision,
                "reasoning": reasoning,
                "vision_result": vision_result,
                "audio_score": audio_score,
                "transaction_value": transaction_value,
                "tenant_id": current_tenant
            }

        except Exception as e:
            print(f"Error in risk evaluation: {e}")
            current_tenant = tenant_id or tenant_manager.get_tenant()
            # Default to BLOCK on error for security
            return {
                "decision": "BLOCK",
                "reasoning": f"Error in AI analysis: {str(e)[:100]}. Blocked for security.",
                "vision_result": vision_result,
                "audio_score": audio_score,
                "transaction_value": transaction_value,
                "tenant_id": current_tenant
            }