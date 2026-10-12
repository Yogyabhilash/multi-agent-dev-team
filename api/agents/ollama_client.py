
import httpx


class OllamaClient:
    """Client for communicating with a locally running Ollama model."""

    def __init__(
        self,
        model: str = "qwen2.5:3b",
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the generated text."""

        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()
        data = response.json()

        generated_text = data.get("response", "").strip()

        if not generated_text:
            raise RuntimeError("Ollama returned an empty response.")

        return generated_text
