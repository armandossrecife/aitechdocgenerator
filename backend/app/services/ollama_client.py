import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3" # Or "qwen:7b", user specified qwen3

async def generate_text(prompt: str, system_prompt: str = "") -> str:
    """
    Calls the local Ollama instance to generate text.
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.3, # Low temp for technical docs
            "top_p": 0.9,
            "num_predict": 4096 # Allow long output
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client: # Long timeout for LLM
        try:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            result = resp.json()
            return result.get("response", "")
        except httpx.RequestError as e:
            print(f"Ollama connection error: {e}")
            return "Error: Could not connect to Ollama. Make sure it is running."
