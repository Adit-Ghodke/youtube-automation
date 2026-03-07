import requests
import logging
import os

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Monitors the status of external APIs."""

    def __init__(self):
        self.pexels_key = os.getenv("PEXELS_API_KEY")

    def check_api_status(self) -> dict:
        """
        Verifies that all required external APIs are accessible.
        Returns a dictionary with the status of each API.
        """
        api_status = {}

        # 1. Check Groq API
        try:
            headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}
            response = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
            if response.status_code == 200:
                api_status["Groq"] = "✅ Online"
            else:
                api_status["Groq"] = f"⚠️ Degraded (Status: {response.status_code})"
        except requests.RequestException as e:
            logger.error(f"Groq health check failed: {e}")
            api_status["Groq"] = "❌ Offline"

        # 2. Check Pexels API
        if self.pexels_key:
            try:
                headers = {"Authorization": self.pexels_key}
                response = requests.get("https://api.pexels.com/v1/search?query=nature&per_page=1", headers=headers, timeout=10)
                if response.status_code == 200:
                    api_status["Pexels"] = "✅ Online"
                else:
                    api_status["Pexels"] = f"⚠️ Degraded (Status: {response.status_code})"
            except requests.RequestException as e:
                logger.error(f"Pexels health check failed: {e}")
                api_status["Pexels"] = "❌ Offline"
        else:
            api_status["Pexels"] = "SKIPPED (No API Key)"
            
        # 3. Check Edge-TTS (Microsoft Speech Service)
        try:
            # Edge-TTS uses Microsoft's speech service
            response = requests.get("https://speech.platform.bing.com", timeout=10)
            if response.status_code in [200, 400, 403]:  # 400/403 expected without auth
                api_status["Edge-TTS"] = "✅ Online"
            else:
                api_status["Edge-TTS"] = f"⚠️ Degraded (Status: {response.status_code})"
        except requests.RequestException as e:
            logger.error(f"Edge-TTS health check failed: {e}")
            api_status["Edge-TTS"] = "❌ Offline"

        return api_status
