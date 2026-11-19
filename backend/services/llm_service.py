"""Language model service initialization using local Ollama."""

import logging
from pipecat.services.ollama.llm import OLLamaLLMService
from backend.config.settings import LLMSettings, get_settings

logger = logging.getLogger("sunrise-clinic.llm")


def create_llm_service(
    llm_settings: LLMSettings | None = None,
) -> OLLamaLLMService:
    """Initialize Ollama LLM service.

    Preserves the local endpoint and lightweight qwen2.5:1.5b model.

    Args:
        llm_settings: Optional LLMSettings instance. If omitted, uses global settings.

    Returns:
        Configured OLLamaLLMService.
    """
    if llm_settings is None:
        llm_settings = get_settings().llm

    logger.info(
        "Connecting to Ollama LLM (model=%s, base_url=%s)",
        llm_settings.model,
        llm_settings.base_url,
    )

    try:
        # Use modern Settings API in Pipecat 1.15+
        settings = OLLamaLLMService.Settings(model=llm_settings.model)
        return OLLamaLLMService(
            base_url=llm_settings.base_url,
            settings=settings,
        )
    except Exception:
        # Fallback to direct model argument for older versions
        return OLLamaLLMService(
            model=llm_settings.model,
            base_url=llm_settings.base_url,
        )
