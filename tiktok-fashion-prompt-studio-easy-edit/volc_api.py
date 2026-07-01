"""Volcengine Ark API wrapper.

This wrapper uses the OpenAI-compatible Chat Completions interface.
Fill ARK_API_KEY and ARK_MODEL_ID in .env.
"""

from __future__ import annotations

import base64
import os
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_secret(name: str, default: str = "") -> str:
    """Read config from environment variables first, then Streamlit secrets.

    This lets the app work both locally with .env and online on Streamlit Cloud
    with secrets configured in Advanced settings.
    """
    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        import streamlit as st  # imported lazily so API wrapper can still be tested outside Streamlit

        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass

    return default


def _get_client() -> OpenAI:
    api_key = get_secret("ARK_API_KEY")
    base_url = get_secret("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

    if not api_key:
        raise RuntimeError("缺少 ARK_API_KEY。请在 .env 或 Streamlit Secrets 里填写火山方舟 API Key。")

    return OpenAI(api_key=api_key, base_url=base_url)


def get_model_id() -> str:
    model_id = get_secret("ARK_MODEL_ID")
    if not model_id:
        raise RuntimeError("缺少 ARK_MODEL_ID。请在 .env 或 Streamlit Secrets 里填写你火山控制台里的模型 ID 或 endpoint ID。")
    return model_id


def encode_image_to_data_url(image_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def call_text_model(prompt: str, temperature: float = 0.7, max_tokens: int = 12000) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=get_model_id(),
        messages=[
            {"role": "system", "content": "你是一个严谨、实用的 TikTok 女装内容策划和视频提示词生成助手。"},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def call_vision_model(
    prompt: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    temperature: float = 0.4,
    max_tokens: int = 16000,
) -> str:
    """Call a multimodal model with one local image.

    Your ARK_MODEL_ID must point to a model/endpoint that supports image understanding.
    """
    client = _get_client()
    data_url = encode_image_to_data_url(image_bytes, mime_type)

    response = client.chat.completions.create(
        model=get_model_id(),
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨、实用的美国 TikTok 女装内容策划和图片分析助手。必须根据图片可见信息分析，不要胡编。",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
