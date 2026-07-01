"""Volcengine Ark / Doubao API wrapper.

Uses the OpenAI-compatible Chat Completions interface.

Recommended Streamlit Secrets for Doubao Seed 2.1 Pro:

ARK_API_KEY = "your_volcengine_ark_api_key"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_SEED21_PRO_MODEL_ID = "your_model_id_or_endpoint_id"

Optional split models:
ARK_TEXT_MODEL_ID = "your_text_model_or_endpoint_id"
ARK_VISION_MODEL_ID = "your_vision_model_or_endpoint_id"

Backward compatible:
ARK_MODEL_ID = "your_model_or_endpoint_id"
"""

from __future__ import annotations

import base64
import os
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


def get_secret(name: str, default: str = "") -> str:
    """Read config from runtime UI, environment variables, then Streamlit secrets.

    Priority:
    1. Runtime config entered in the app UI for temporary testing.
    2. Environment variables / local .env.
    3. Streamlit Secrets for production deployment.
    """
    try:
        import streamlit as st

        runtime_config = st.session_state.get("runtime_api_config", {})
        value = str(runtime_config.get(name, "")).strip()
        if value:
            return value
    except Exception:
        pass

    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass

    return default


def _get_client() -> OpenAI:
    api_key = get_secret("ARK_API_KEY")
    base_url = get_secret("ARK_BASE_URL", DEFAULT_ARK_BASE_URL)

    if not api_key:
        raise RuntimeError("缺少 ARK_API_KEY。请在 Streamlit Secrets 里填写火山方舟 API Key。")

    return OpenAI(api_key=api_key, base_url=base_url, timeout=60.0)


def get_text_model_id() -> str:
    model_id = (
        get_secret("ARK_TEXT_MODEL_ID")
        or get_secret("DOUBAO_SEED21_PRO_MODEL_ID")
        or get_secret("ARK_MODEL_ID")
    )
    if not model_id:
        raise RuntimeError(
            "缺少模型 ID。请在 Streamlit Secrets 里填写 DOUBAO_SEED21_PRO_MODEL_ID，"
            "或 ARK_TEXT_MODEL_ID / ARK_MODEL_ID。"
        )
    return model_id


def get_vision_model_id() -> str:
    model_id = (
        get_secret("ARK_VISION_MODEL_ID")
        or get_secret("DOUBAO_SEED21_PRO_MODEL_ID")
        or get_secret("ARK_TEXT_MODEL_ID")
        or get_secret("ARK_MODEL_ID")
    )
    if not model_id:
        raise RuntimeError(
            "缺少视觉/多模态模型 ID。请在 Streamlit Secrets 里填写 DOUBAO_SEED21_PRO_MODEL_ID，"
            "或 ARK_VISION_MODEL_ID / ARK_MODEL_ID。"
        )
    return model_id


def get_api_status() -> Dict[str, str]:
    """Expose non-sensitive API status for UI display."""
    has_key = bool(get_secret("ARK_API_KEY"))
    base_url = get_secret("ARK_BASE_URL", DEFAULT_ARK_BASE_URL)

    text_model = (
        get_secret("ARK_TEXT_MODEL_ID")
        or get_secret("DOUBAO_SEED21_PRO_MODEL_ID")
        or get_secret("ARK_MODEL_ID")
        or "未配置"
    )
    vision_model = (
        get_secret("ARK_VISION_MODEL_ID")
        or get_secret("DOUBAO_SEED21_PRO_MODEL_ID")
        or get_secret("ARK_TEXT_MODEL_ID")
        or get_secret("ARK_MODEL_ID")
        or "未配置"
    )

    return {
        "api_key_configured": "已配置" if has_key else "未配置",
        "base_url": base_url,
        "text_model": text_model,
        "vision_model": vision_model,
        "image_input_mode": get_secret("ARK_IMAGE_INPUT_MODE", "data_url"),
    }


def get_image_input_mode() -> str:
    """Image payload mode for Volcengine Ark vision calls.

    data_url: OpenAI style, data:image/jpeg;base64,...
    raw_base64: only the base64 string. Some Volcengine docs describe Base64 input this way.
    """
    mode = get_secret("ARK_IMAGE_INPUT_MODE", "data_url").strip().lower()
    if mode not in {"data_url", "raw_base64"}:
        return "data_url"
    return mode


def encode_image_for_api(image_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    if get_image_input_mode() == "raw_base64":
        return encoded
    return f"data:{mime_type};base64,{encoded}"


def call_text_model(prompt: str, temperature: float = 0.7, max_tokens: int = 12000) -> str:
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=get_text_model_id(),
            messages=[
                {"role": "system", "content": "你是一个严谨、实用的 TikTok 女装内容策划和视频提示词生成助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        raise RuntimeError(f"文本模型调用失败：{type(exc).__name__}: {exc}") from exc


def call_vision_model(
    prompt: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    temperature: float = 0.4,
    max_tokens: int = 16000,
) -> str:
    client = _get_client()
    image_payload = encode_image_for_api(image_bytes, mime_type)

    print(f"[vision-call] model={get_vision_model_id()} bytes={len(image_bytes)} mime={mime_type} mode={get_image_input_mode()}")
    try:
        response = client.chat.completions.create(
            model=get_vision_model_id(),
            messages=[
                {
                    "role": "system",
                    "content": "你是一个严谨、实用的美国 TikTok 女装内容策划和图片分析助手。必须根据图片可见信息分析，不要胡编。",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_payload, "detail": "low"}},
                    ],
                },
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        raise RuntimeError(
            f"图片理解模型调用失败：{type(exc).__name__}: {exc}\n"
            "排查方向：1) Vision Model 是否支持 image_url 图片输入；"
            "2) 图片是否过大；3) Endpoint ID 是否正确；4) API Key 是否有权限。"
        ) from exc
