"""
LLM routing service for configuring CrewAI LLM instances.
"""
import os
import logging
from typing import Optional, Tuple
from crewai import LLM

import config
from .database import get_setting

logger = logging.getLogger(__name__)

def get_llm(provider: str, api_key: str, model_name: Optional[str] = None, temperature: float = config.DEFAULT_TEMPERATURE) -> LLM:
  """Returns a CrewAI LLM instance based on the provider."""
  provider = provider.lower().strip()
  
  if provider == 'gemini':
    os.environ['GEMINI_API_KEY'] = api_key
    os.environ['GOOGLE_API_KEY'] = api_key
    model = model_name or config.DEFAULT_MODELS.get('gemini', 'gemini/gemini-3.8-flash')
    return LLM(model=model, temperature=temperature)
    
  elif provider == 'openai':
    os.environ['OPENAI_API_KEY'] = api_key
    model = model_name or config.DEFAULT_MODELS.get('openai', 'gpt-4o-mini')
    return LLM(model=model, temperature=temperature)
    
  elif provider == 'ollama':
    # Bypass OpenAI API key validation if ollama tries to look for it
    os.environ['OPENAI_API_KEY'] = 'NA'
    model = model_name or config.DEFAULT_MODELS.get('ollama', 'ollama/llama3.2')
    return LLM(model=model, base_url='http://localhost:11434', temperature=temperature)
    
  elif provider == 'groq':
    os.environ['GROQ_API_KEY'] = api_key
    model = model_name or config.DEFAULT_MODELS.get('groq', 'groq/openai/gpt-oss-120b')
    # Limit max_tokens to 4000 so the final JSON report fits all candidates
    llm = LLM(model=model, temperature=temperature, max_tokens=4000)
    
    # Monkeypatch to strip unsupported cache_breakpoint injected by litellm/crewai
    original_call = llm.call
    def patched_call(messages, *args, **kwargs):
      for m in messages:
        if 'cache_breakpoint' in m:
          del m['cache_breakpoint']
      return original_call(messages, *args, **kwargs)
    llm.call = patched_call
    return llm
    
  else:
    raise ValueError(f"Unsupported LLM provider: {provider}")

def validate_api_key(provider: str, api_key: str) -> Tuple[bool, str]:
  """Basic validation for API keys."""
  provider = provider.lower().strip()
  
  if provider == 'ollama':
    return True, "Ollama does not require an API key."
    
  if not api_key or not api_key.strip():
    return False, "API key cannot be empty."
    
  if provider == 'openai' and not api_key.startswith('sk-'):
    return False, "OpenAI API key usually starts with 'sk-'."
    
  if provider == 'groq' and not api_key.startswith('gsk_'):
    return False, "Groq API key usually starts with 'gsk_'."
    
  if provider == 'gemini' and not (api_key.startswith('AIza') or api_key.startswith('AQ.')):
    return False, "Gemini API key usually starts with 'AIza' or 'AQ.'."
    
  return True, "API key format appears valid."

def get_llm_from_settings() -> Optional[LLM]:
  """Retrieves an LLM instance based on database settings."""
  try:
    provider = get_setting('llm_provider')
    api_key = get_setting('api_key')
    model = get_setting('llm_model')
    temperature_str = get_setting('llm_temperature')
    
    if not provider:
      logger.warning("No LLM provider configured in settings.")
      return None
      
    temperature = float(temperature_str) if temperature_str else config.DEFAULT_TEMPERATURE
    
    return get_llm(
      provider=provider,
      api_key=api_key or "",
      model_name=model,
      temperature=temperature
    )
  except Exception as e:
    logger.error(f"Failed to initialize LLM from settings: {e}")
    return None
