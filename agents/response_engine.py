import asyncio
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

class ResponseEngine:
    def __init__(self):
        self.function_url = os.getenv("AZURE_FUNCTION_URL")
        self.session = aiohttp.ClientSession()

    async def handle_response(self, evaluation_result: dict):
        """
        Handle the orchestrator's evaluation result.
        Trigger soft lock if decision is BLOCK.
        """
        if evaluation_result["decision"] == "BLOCK":
            await self._trigger_soft_lock(evaluation_result)

    async def _trigger_soft_lock(self, evaluation_result: dict):
        """
        Trigger Azure Function to soft lock the account.
        """
        payload = {
            "action": "soft_lock",
            "reason": evaluation_result["reasoning"],
            "vision_score": evaluation_result["vision_score"],
            "acoustic_score": evaluation_result["acoustic_score"],
            "transaction_amount": evaluation_result["transaction_amount"]
        }

        try:
            async with self.session.post(self.function_url, json=payload) as response:
                if response.status == 200:
                    print("Soft lock triggered successfully")
                else:
                    print(f"Failed to trigger soft lock: {response.status} - {await response.text()}")
        except Exception as e:
            print(f"Error triggering soft lock: {e}")

    async def close(self):
        """Close the session."""
        await self.session.close()