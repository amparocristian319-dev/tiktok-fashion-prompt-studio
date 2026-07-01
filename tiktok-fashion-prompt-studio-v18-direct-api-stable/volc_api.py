"""Direct Volcengine Ark / OpenAI-compatible API wrapper.

V18 uses direct HTTPS requests instead of the OpenAI Python client.
This makes timeouts and error messages more predictable on Streamlit Cloud.
"""

from __future__ import annotations

import base64
import os
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


def get_secret(name: str, default: str = "") -> str:
    """Read config from runtime UI, environment variables, then Streamlit secrets."""
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


def _normalize_base_url(base_url: str) -> str:
    return (base_url or DEFAULT_ARK_BASE_URL).rstrip("/")


def _chat_completions_url() -> str:
    return f"{_normalize_base_url(get_secret('ARK_BASE_URL', DEFAULT_ARK_BASE_URL))}/chat/completions"


def _headers() -> Dict[str, str]:
    api_key = get_secret("ARK_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 API Key。请先在模型接入中心或后台配置中填写。")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def get_text_model_id() -> str:
    model_id = (
        get_secret("ARK_TEXT_MODEL_ID")
        or get_secret("DOUBAO_SEED21_PRO_MODEL_ID")
        or get_secret("ARK_MODEL_ID")
    )
    if not model_id:
        raise RuntimeError("缺少文本模型 ID。请先在模型接入中心或后台配置中填写。")
    return model_id


def get_vision_model_id() -> str:
    model_id = (
        get_secret("ARK_VISION_MODEL_ID")
        or get_secret("DOUBAO_SEED21_PRO_MODEL_ID")
        or get_secret("ARK_TEXT_MODEL_ID")
        or get_secret("ARK_MODEL_ID")
    )
    if not model_id:
        raise RuntimeError("缺少图片理解模型 ID。请先在模型接入中心或后台配置中填写。")
    return model_id


def get_api_status() -> Dict[str, str]:
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
    mode = get_secret("ARK_IMAGE_INPUT_MODE", "data_url").strip().lower()
    return mode if mode in {"data_url", "raw_base64"} else "data_url"


def encode_image_for_api(image_bytes: bytes, mime_type: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    if get_image_input_mode() == "raw_base64":
        return encoded
    return f"data:{mime_type};base64,{encoded}"


def _extract_content(response_json: Dict[str, Any]) -> str:
    try:
        return response_json["choices"][0]["message"]["content"] or ""
    except Exception as exc:
        raise RuntimeError(f"模型返回格式异常：{response_json}") from exc


def _post_chat(payload: Dict[str, Any], request_type: str) -> str:
    url = _chat_completions_url()
    model = payload.get("model", "")
    try:
        print(f"[api-request] type={request_type} url={url} model={model}")
        resp = requests.post(
            url,
            headers=_headers(),
            json=payload,
            timeout=(8, 35),
        )
        print(f"[api-response] type={request_type} status={resp.status_code}")
    except requests.Timeout as exc:
        raise RuntimeError(f"{request_type} 请求超时：服务未在 35 秒内返回。请稍后重试或换更轻量图片。") from exc
    except requests.RequestException as exc:
        raise RuntimeError(f"{request_type} 网络请求失败：{exc}") from exc

    if resp.status_code >= 400:
        body = resp.text[:1200]
        raise RuntimeError(f"{request_type} 请求失败，HTTP {resp.status_code}：{body}")

    try:
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"{request_type} 返回不是有效 JSON：{resp.text[:1000]}") from exc

    return _extract_content(data)


def call_text_model(prompt: str, temperature: float = 0.7, max_tokens: int = 12000) -> str:
    payload = {
        "model": get_text_model_id(),
        "messages": [
            {"role": "system", "content": "你是一个严谨、实用的 TikTok 女装内容策划和视频提示词生成助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return _post_chat(payload, "文本生成")


def call_vision_model(
    prompt: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    temperature: float = 0.1,
    max_tokens: int = 700,
) -> str:
    image_payload = encode_image_for_api(image_bytes, mime_type)
    print(f"[vision-payload] model={get_vision_model_id()} bytes={len(image_bytes)} mime={mime_type} mode={get_image_input_mode()}")

    payload = {
        "model": get_vision_model_id(),
        "messages": [
            {
                "role": "system",
                "content": "你只做服装图片的快速视觉识别。只基于图片可见信息回答，不要长篇推理，不要创意策划。",
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_payload}},
                    {"type": "text", "text": prompt},
                ],
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return _post_chat(payload, "图片识别")
