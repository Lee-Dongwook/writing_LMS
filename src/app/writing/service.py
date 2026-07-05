import base64
import io
import json
import logging
import os
import re
import time
from io import BytesIO
from typing import IO, Any

import pymupdf as fitz
from fastapi import HTTPException, UploadFile
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Length, Pt

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def empty_str_to_none(v: Any) -> Any | None:  # noqa: ANN401
    """Pydantic validator to convert empty strings to None."""
    if isinstance(v, str) and v == "":
        return None
    return v
