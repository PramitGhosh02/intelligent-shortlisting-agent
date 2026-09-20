"""
Intelligent Candidate Shortlisting Agent - Custom Gradio Theme

Professional indigo/blue theme with card-style layouts.
"""

import gradio as gr


def get_theme() -> gr.themes.Soft:
  """Returns the custom Gradio theme for the application."""
  return gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="blue",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
  ).set(
    body_background_fill="#f1f5f9",
    block_background_fill="#ffffff",
    block_border_width="1px",
    block_border_color="#e2e8f0",
    block_shadow="0 1px 3px 0 rgb(0 0 0 / 0.1)",
    block_label_text_color="#475569",
    button_primary_background_fill="*primary_600",
    button_primary_background_fill_hover="*primary_700",
    button_primary_text_color="#ffffff",
    button_secondary_background_fill="#f8fafc",
    button_secondary_background_fill_hover="#f1f5f9",
    input_background_fill="#ffffff",
    input_border_color="#cbd5e1",
  )


CUSTOM_CSS = """
/* KPI metric cards */
.metric-card {
  border-left: 4px solid #4f46e5 !important;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
  border-radius: 10px !important;
  padding: 8px 12px !important;
}

/* Score badges */
.score-excellent {
  color: #16a34a !important;
  font-weight: 700 !important;
}
.score-good {
  color: #ca8a04 !important;
  font-weight: 700 !important;
}
.score-poor {
  color: #dc2626 !important;
  font-weight: 700 !important;
}

/* Header styling */
.app-header {
  text-align: center;
  padding: 16px !important;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
  border-radius: 12px !important;
  color: white !important;
  margin-bottom: 8px !important;
}
.app-header h1, .app-header p {
  color: white !important;
}

/* Status badges */
.status-sent {
  color: #16a34a !important;
  font-weight: 600 !important;
}
.status-pending {
  color: #ca8a04 !important;
  font-weight: 600 !important;
}
.status-failed {
  color: #dc2626 !important;
  font-weight: 600 !important;
}

/* Tab styling */
.tab-nav button {
  font-weight: 600 !important;
  font-size: 14px !important;
}

/* Progress area */
.progress-area {
  border: 1px dashed #cbd5e1 !important;
  border-radius: 8px !important;
  padding: 12px !important;
  background: #f8fafc !important;
}

/* Dark mode overrides */
.dark .metric-card {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
  border-left-color: #818cf8 !important;
}
.dark .app-header {
  background: linear-gradient(135deg, #3730a3 0%, #5b21b6 100%) !important;
}
.dark .progress-area {
  background: #1e293b !important;
  border-color: #334155 !important;
  color: #f8fafc !important;
}
"""
