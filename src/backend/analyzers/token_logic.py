# src/backend/token_estimator.py

from dataclasses import dataclass

# ---- MODEL DEFINITIONS ----

@dataclass
class LLMModel:
    provider: str
    name: str
    max_tokens: int


MODELS = [
    # Google Gemini
    LLMModel("Google Gemini", "Gemini 1.5 Pro", 2_000_000),
    LLMModel("Google Gemini", "Gemini 3 Pro", 1_048_576),
    LLMModel("Google Gemini", "Gemini 3 Flash", 1_048_576),

    # Anthropic Claude
    LLMModel("Anthropic Claude", "Claude 4.5 Sonnet", 1_000_000),
    LLMModel("Anthropic Claude", "Claude 4.5 Opus", 1_000_000),
    LLMModel("Anthropic Claude", "Claude 4.0", 200_000),

    # OpenAI
    LLMModel("OpenAI", "GPT-5.2 (API)", 400_000),
    LLMModel("OpenAI", "GPT-5.1 (Standard)", 272_144),
    LLMModel("OpenAI", "o3 / o4-mini", 200_000),
]


# ---- CORE LOGIC ----

def estimate_tokens_from_text(text: str) -> int:
    """
    Offline token estimation.
    Rule of thumb: 1 token ~= 4 characters
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


def analyze_models(estimated_tokens: int):
    """
    Compare estimated tokens against all models.
    Returns structured results for UI.
    """
    results = []

    for model in MODELS:
        remaining = model.max_tokens - estimated_tokens

        # Categorize
        if remaining < 0:
            status = "overflow"
        elif remaining < model.max_tokens * 0.2:
            status = "tight"
        else:
            status = "safe"

        results.append({
            "provider": model.provider,
            "name": model.name,
            "limit": model.max_tokens,
            "remaining": remaining,
            "status": status
        })

    return results


def overall_token_status(model_analysis: list) -> str:
    """
    Determines overall safety status.
    Returns: 'safe' or 'overflow'
    """

    for model in model_analysis:
        if model["status"] in ("safe", "tight"):
            return "safe"

    return "overflow"
