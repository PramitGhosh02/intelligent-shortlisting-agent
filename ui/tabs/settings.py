"""
Tab 6: Settings

Configuration for LLM provider, API keys, model selection, and SMTP email settings.
All settings are persisted to SQLite.
"""

import gradio as gr
import traceback

import config


def load_settings() -> tuple:
  """Loads saved settings from the database. Returns field values."""
  try:
    from services.database import get_all_settings

    s = get_all_settings()
    return (
      s.get("llm_provider", config.DEFAULT_LLM_PROVIDER),
      s.get("api_key", ""),
      s.get("llm_model", ""),
      s.get("smtp_server", config.DEFAULT_SMTP_SERVER),
      int(s.get("smtp_port", str(config.DEFAULT_SMTP_PORT))),
      s.get("smtp_username", ""),
      s.get("smtp_password", ""),
      s.get("smtp_sender", ""),
    )
  except Exception:
    return (
      config.DEFAULT_LLM_PROVIDER, "", "",
      config.DEFAULT_SMTP_SERVER, config.DEFAULT_SMTP_PORT,
      "", "", "",
    )


def save_llm_settings(provider: str, api_key: str, model: str) -> str:
  """Saves LLM settings to the database."""
  try:
    from services.database import save_setting

    save_setting("llm_provider", provider)
    save_setting("api_key", api_key)
    save_setting("llm_model", model)
    return " LLM settings saved successfully."
  except Exception as e:
    return f" Error saving settings: {str(e)}"


def save_smtp_settings(server: str, port: int, username: str,
            password: str, sender: str) -> str:
  """Saves SMTP settings to the database."""
  try:
    from services.database import save_setting

    save_setting("smtp_server", server)
    save_setting("smtp_port", str(int(port)))
    save_setting("smtp_username", username)
    save_setting("smtp_password", password)
    save_setting("smtp_sender", sender or username)
    return " SMTP settings saved successfully."
  except Exception as e:
    return f" Error saving SMTP settings: {str(e)}"


def test_llm_connection(provider: str, api_key: str, model: str) -> str:
  """Tests the LLM connection by sending a simple prompt."""
  try:
    from services.llm_router import get_llm, validate_api_key

    # Validate API key first
    if provider != "ollama":
      valid, msg = validate_api_key(provider, api_key)
      if not valid:
        return f" {msg}"

    # Try creating the LLM instance
    llm = get_llm(provider, api_key, model or None)
    return f" Successfully connected to {provider} ({model or 'default model'})!"

  except Exception as e:
    traceback.print_exc()
    return f" Connection failed: {str(e)}"


def test_smtp_connection(server: str, port: int, username: str, password: str) -> str:
  """Tests SMTP connection."""
  try:
    from services.email_service import test_smtp_connection as test_smtp

    smtp_config = {
      "server": server,
      "port": int(port),
      "username": username,
      "password": password,
    }
    success, msg = test_smtp(smtp_config)
    return f"{'' if success else ''} {msg}"

  except Exception as e:
    return f" SMTP test failed: {str(e)}"


def get_models_for_provider(provider: str) -> gr.update:
  """Returns available models for the selected provider."""
  models = config.LLM_MODELS.get(provider, [])
  default = config.DEFAULT_MODELS.get(provider, "")
  return gr.update(choices=models, value=default)


def create_settings_tab() -> dict:
  """Creates the Settings tab and returns component references."""
  
  # Load initial values from the database
  (
    init_provider, init_api_key, init_model,
    init_smtp_server, init_smtp_port,
    init_smtp_username, init_smtp_password, init_smtp_sender
  ) = load_settings()

  with gr.Tab(" Settings", id="settings"):
    gr.Markdown("### Application Settings\nConfigure your LLM provider, API keys, and email settings. All settings are saved automatically.")

    with gr.Row():
      # LLM Settings Column
      with gr.Column():
        gr.Markdown("#### LLM Configuration")

        llm_provider = gr.Dropdown(
          label="LLM Provider",
          choices=["gemini", "openai", "ollama", "groq"],
          value=init_provider,
          info="Select your AI provider. Gemini offers a free tier.",
        )
        api_key = gr.Textbox(
          label="API Key",
          type="password",
          value=init_api_key,
          placeholder="Paste your API key here...",
          info="Not required for Ollama (local models).",
        )
        llm_model = gr.Dropdown(
          label="Model",
          choices=config.LLM_MODELS.get(init_provider, config.LLM_MODELS.get(config.DEFAULT_LLM_PROVIDER, [])),
          value=init_model if init_model else config.DEFAULT_MODELS.get(init_provider, ""),
          info="Choose the model to use.",
        )

        with gr.Row():
          save_llm_btn = gr.Button(" Save LLM Settings", variant="primary")
          test_llm_btn = gr.Button(" Test Connection", variant="secondary")

        llm_status = gr.Markdown("")

        gr.Markdown("---")
        gr.Markdown(
          "** Getting an API Key:**\n"
          "- **Gemini (Free):** [Google AI Studio](https://aistudio.google.com/apikey) -> Create API Key\n"
          "- **OpenAI:** [platform.openai.com](https://platform.openai.com/api-keys) -> Create new secret key\n"
          "- **Ollama (Free, Local):** Install from [ollama.com](https://ollama.com), run `ollama pull llama3.2`"
        )

      # SMTP Settings Column
      with gr.Column():
        gr.Markdown("#### Email (SMTP) Configuration")

        smtp_server = gr.Textbox(
          label="SMTP Server",
          value=init_smtp_server,
          placeholder="smtp.gmail.com",
        )
        smtp_port = gr.Number(
          label="SMTP Port",
          value=init_smtp_port,
          minimum=1,
          maximum=65535,
        )
        smtp_username = gr.Textbox(
          label="Email Username",
          value=init_smtp_username,
          placeholder="your.email@gmail.com",
        )
        smtp_password = gr.Textbox(
          label="Email Password / App Password",
          type="password",
          value=init_smtp_password,
          placeholder="App-specific password",
          info="For Gmail, use an App Password (not your regular password).",
        )
        smtp_sender = gr.Textbox(
          label="Sender Email (optional)",
          value=init_smtp_sender,
          placeholder="Same as username if empty",
        )

        with gr.Row():
          save_smtp_btn = gr.Button(" Save Email Settings", variant="primary")
          test_smtp_btn = gr.Button(" Test SMTP", variant="secondary")

        smtp_status = gr.Markdown("")

    # ── Event Handlers ────────────────────────────────────────

    # Update model dropdown when provider changes
    llm_provider.change(
      fn=get_models_for_provider,
      inputs=[llm_provider],
      outputs=[llm_model],
    )

    # Save LLM settings
    save_llm_btn.click(
      fn=save_llm_settings,
      inputs=[llm_provider, api_key, llm_model],
      outputs=[llm_status],
    )

    # Test LLM connection
    test_llm_btn.click(
      fn=test_llm_connection,
      inputs=[llm_provider, api_key, llm_model],
      outputs=[llm_status],
    )

    # Save SMTP settings
    save_smtp_btn.click(
      fn=save_smtp_settings,
      inputs=[smtp_server, smtp_port, smtp_username, smtp_password, smtp_sender],
      outputs=[smtp_status],
    )

    # Test SMTP connection
    test_smtp_btn.click(
      fn=test_smtp_connection,
      inputs=[smtp_server, smtp_port, smtp_username, smtp_password],
      outputs=[smtp_status],
    )

  return {
    "llm_provider": llm_provider,
    "api_key": api_key,
    "llm_model": llm_model,
    "smtp_server": smtp_server,
    "smtp_port": smtp_port,
    "smtp_username": smtp_username,
    "smtp_password": smtp_password,
    "smtp_sender": smtp_sender,
    "llm_status": llm_status,
    "smtp_status": smtp_status,
  }
