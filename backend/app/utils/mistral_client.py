"""Mistral API client."""
from app.config import settings


class MistralClient:
    @staticmethod
    async def generate(prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 150) -> str:
        """Generate text using Mistral API."""
        if not settings.MISTRAL_API_KEY:
            return ""
        
        # Import here to avoid circular imports
        import httpx
        
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": settings.DEFAULT_LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return ""
