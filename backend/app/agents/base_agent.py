import asyncio
import httpx
from typing import List, Dict, Any, Callable

class BaseAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.logs: List[str] = []
        self._log_callback: Callable[[str], None] = None

    def set_log_callback(self, callback: Callable[[str], None]):
        self._log_callback = callback

    def log(self, message: str):
        formatted_message = f"[{self.name}] {message}"
        self.logs.append(formatted_message)
        print(formatted_message)
        if self._log_callback:
            self._log_callback(formatted_message)

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent logic.
        Must be overridden by child classes.
        """
        self.log(f"Starting execution for prompt: {state.get('user_prompt')}")
        await asyncio.sleep(0.5)
        return state

    async def call_llm(self, state: Dict[str, Any], system_prompt: str, user_prompt: str) -> str:
        """
        Calls the LLM selected in state['settings'] or falls back to simulated responses if not configured.
        """
        settings = state.get("settings", {})
        provider = settings.get("provider", "simulated")
        api_key = settings.get("apiKey", "")
        model = settings.get("model", "")
        api_url = settings.get("apiUrl", "")

        if not api_key:
            import os
            api_key = os.environ.get("API_KEY") or os.environ.get("GEMINI_API_KEY") or ""

        if provider == "simulated" or (not api_key and provider in ["openai", "gemini"]):
            self.log("Running in simulated mode (no API key or simulated provider selected).")
            return ""

        self.log(f"Contacting {provider.upper()} API using model '{model}'...")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if provider == "gemini":
                    # Call Gemini API
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                    payload = {
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": f"{system_prompt}\n\nUser Request: {user_prompt}"}]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.2,
                            "topP": 0.95,
                        }
                    }
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]

                elif provider == "openai":
                    # Call OpenAI API
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2
                    }
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    return data["choices"][0]["message"]["content"]

                elif provider == "ollama":
                    # Call Ollama API
                    url = f"{api_url or 'http://localhost:11434'}/api/chat"
                    payload = {
                        "model": model or "llama3",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "stream": False
                    }
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return data["message"]["content"]

        except Exception as e:
            self.log(f"Error calling LLM: {str(e)}. Falling back to simulation.")
            return ""

        return ""
