from app.providers.openai_llm import OpenAILLMAdapter


class GeminiLLMAdapter(OpenAILLMAdapter):
    """Google Gemini LLM Adapter using the OpenAI-compatible endpoint.
    Defaults to gemini-flash-lite-latest model with 30s timeout and 2048 max tokens.
    Adheres strictly to the LLMProvider protocol.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-flash-lite-latest",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/",
        timeout: float = 30.0,
        max_tokens: int = 2048,
    ):
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout=timeout,
            max_tokens=max_tokens,
        )
