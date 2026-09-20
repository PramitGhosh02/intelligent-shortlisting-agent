"""
Resume parsing service for extracting text from PDF and DOCX files.
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Union, Any
import fitz # PyMuPDF
from docx import Document

import config

logger = logging.getLogger(__name__)

def parse_pdf(file_path: str) -> str:
  """Extracts text from a PDF file."""
  text = []
  try:
    with fitz.open(file_path) as doc:
      for page in doc:
        text.append(page.get_text())
    return "\n".join(text)
  except Exception as e:
    logger.error(f"Failed to parse PDF {file_path}: {e}")
    return ""

def parse_docx(file_path: str) -> str:
  """Extracts text from a DOCX file."""
  text = []
  try:
    doc = Document(file_path)
    for para in doc.paragraphs:
      if para.text.strip():
        text.append(para.text)
    return "\n".join(text)
  except Exception as e:
    logger.error(f"Failed to parse DOCX {file_path}: {e}")
    return ""

def parse_resume(file_path: str) -> str:
  """Detects file extension and extracts text appropriately."""
  ext = os.path.splitext(file_path)[1].lower()
  
  if ext not in config.SUPPORTED_RESUME_EXTENSIONS:
    logger.error(f"Unsupported file type: {ext}")
    raise ValueError(f"Unsupported file type: {ext}. Supported types: {config.SUPPORTED_RESUME_EXTENSIONS}")
    
  if ext == '.pdf':
    return parse_pdf(file_path)
  elif ext == '.docx':
    return parse_docx(file_path)
    
  return ""

def save_uploaded_file(file_obj: Any, filename: str) -> str:
  """Saves an uploaded file to the configured uploads directory."""
  try:
    os.makedirs(config.UPLOADS_DIR, exist_ok=True)
    save_path = os.path.join(config.UPLOADS_DIR, filename)
    
    if isinstance(file_obj, str):
      # It's a file path string
      shutil.copy(file_obj, save_path)
    else:
      # It's a file-like object
      if hasattr(file_obj, 'name') and os.path.exists(file_obj.name):
        shutil.copy(file_obj.name, save_path)
      elif hasattr(file_obj, 'read'):
        with open(save_path, 'wb') as f:
          shutil.copyfileobj(file_obj, f)
      else:
        raise ValueError("Unsupported file object format")
        
    return str(save_path)
  except Exception as e:
    logger.error(f"Failed to save uploaded file: {e}")
    raise
