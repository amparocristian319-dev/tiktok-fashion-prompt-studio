"""Stable direct API wrapper for TikTok Fashion Prompt Studio.

V22 fixes:
- Asset recognition: no deep thinking, 120s timeout.
- Prompt generation: deep thinking enabled, longer timeout.
- Direct POST to /chat/completions, no SDK wrapper.
- Official image payload default: data:image/jpeg;base64,...
- Hidden diagnostics recorded in Streamlit session_state.
"""

from __future__ import annotations

import base64
import os
import time
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


def get_secret(name: str, default: str = "") -> str:
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


def _bounded_timeout(raw: str, default: int) -> int:
    try:
        value = int(str(raw).strip())
    except Exception:
        value = default
    return max(60, min(value, 300))


def get_request_timeout_seconds() -> int:
    return _bounded_timeout(get_secret("ARK_REQUEST_TIMEOUT", "180"), 180)


def get_asset_timeout_seconds() -> int:
    return _bounded_timeout(get_secret("ARK_ASSET_TIMEOUT", "120"), 120)


def get_generation_timeout_seconds() -> int:
    return _bounded_timeout(get_secret("ARK_GENERATION_TIMEOUT", "240"), 240)


def _record_api_event(event: Dict[str, Any]) -> None:
    try:
        import streamlit as st
        st.session_state["last_api_event"] = {**event, "ts": time.strftime("%H:%M:%S")}
    except Exception:
        pass


def _base_url() -> str:
    return (get_secret("ARK_BASE_URL", DEFAULT_ARK_BASE_URL) or DEFAULT_ARK_BASE_URL).rstrip("/")


def _chat_url() -> str:
    return f"{_base_url()}/chat/completions"


def _headers() -> Dict[str, str]:
    api_key = get_secret("ARK_API_KEY")
    if not api_key:
        _record_api_event({"stage": "missing_api_key"})
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
        _record_api_event({"stage": "missing_text_model"})
        raise RuntimeError("缺少文本模型 ID。请先在模型接入中心或后台配置中填写。")
    return model_id


def get_vision_model_id() -> str:
    # Do not silently fall back to ARK_TEXT_MODEL_ID.
    # If using split endpoints, configure ARK_VISION_MODEL_ID explicitly.
    model_id = (
        get_secret("ARK_VISION_MODEL_ID")
        or get_secret("DOUBAO_SEED21_PRO_MODEL_ID")
        or get_secret("ARK_MODEL_ID")
    )
    if not model_id:
        _record_api_event({"stage": "missing_vision_model"})
        raise RuntimeError("缺少图片识别模型 ID。请配置 ARK_VISION_MODEL_ID 或 DOUBAO_SEED21_PRO_MODEL_ID。")
    return model_id


def get_image_input_mode() -> str:
    mode = get_secret("ARK_IMAGE_INPUT_MODE", "data_url").strip().lower()
    return mode if mode in {"data_url", "raw_base64"} else "data_url"


def get_api_status() -> Dict[str, str]:
    has_key = bool(get_secret("ARK_API_KEY"))
    return {
        "api_key_configured": "已配置" if has_key else "未配置",
        "base_url": get_secret("ARK_BASE_URL", DEFAULT_ARK_BASE_URL),
        "text_model": get_text_model_id() if (get_secret("ARK_TEXT_MODEL_ID") or get_secret("DOUBAO_SEED21_PRO_MODEL_ID") or get_secret("ARK_MODEL_ID")) else "未配置",
        "vision_model": get_vision_model_id() if (get_secret("ARK_VISION_MODEL_ID") or get_secret("DOUBAO_SEED21_PRO_MODEL_ID") or get_secret("ARK_MODEL_ID")) else "未配置",
        "image_input_mode": get_image_input_mode(),
        "request_timeout": str(get_request_timeout_seconds()),
        "asset_timeout": str(get_asset_timeout_seconds()),
        "generation_timeout": str(get_generation_timeout_seconds()),
    }


def _encode_image(image_bytes: bytes, mime_type: str, mode: str) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    if mode == "raw_base64":
        return encoded
    return f"data:{mime_type};base64,{encoded}"


def _extract_content(data: Dict[str, Any]) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"模型返回格式异常：{str(data)[:1000]}") from exc

    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif item.get("type") == "text":
                    parts.append(str(item.get("content", "")))
        return "\n".join(p for p in parts if p).strip()

    return str(content or "").strip()


def _post_chat(
    payload: Dict[str, Any],
    request_type: str,
    timeout_seconds: Optional[int] = None,
    retry: int = 1,
) -> str:
    timeout_seconds = timeout_seconds or get_request_timeout_seconds()
    url = _chat_url()
    model = payload.get("model", "")
    last_error: Optional[Exception] = None

    for attempt in range(1, retry + 2):
        start = time.time()
        _record_api_event({
            "stage": "request_started",
            "type": request_type,
            "attempt": attempt,
            "url": url,
            "model": model,
            "timeout": timeout_seconds,
        })
        print(f"[api-request] type={request_type} attempt={attempt} model={model} timeout={timeout_seconds}")

        try:
            response = requests.post(
                url,
                headers=_headers(),
                json=payload,
                timeout=(10, timeout_seconds),
            )
            elapsed = round(time.time() - start, 2)
            _record_api_event({
                "stage": "response_received",
                "type": request_type,
                "attempt": attempt,
                "status": response.status_code,
                "elapsed": elapsed,
                "model": model,
            })
            print(f"[api-response] type={request_type} status={response.status_code} elapsed={elapsed}s")

            if response.status_code >= 400:
                body = response.text[:1500]
                _record_api_event({
                    "stage": "http_error",
                    "type": request_type,
                    "status": response.status_code,
                    "body": body,
                    "model": model,
                })
                raise RuntimeError(f"{request_type}请求失败，HTTP {response.status_code}：{body}")

            try:
                data = response.json()
            except Exception as exc:
                raise RuntimeError(f"{request_type}返回不是有效 JSON：{response.text[:1000]}") from exc

            content = _extract_content(data)
            if not content:
                _record_api_event({"stage": "empty_content", "type": request_type, "model": model})
            return content

        except requests.Timeout as exc:
            last_error = exc
            _record_api_event({
                "stage": "timeout",
                "type": request_type,
                "attempt": attempt,
                "model": model,
                "timeout": timeout_seconds,
            })
            if attempt <= retry:
                time.sleep(1.2)
                continue
            raise RuntimeError(f"{request_type}请求超时：{timeout_seconds} 秒内没有返回。") from exc

        except requests.RequestException as exc:
            last_error = exc
            _record_api_event({
                "stage": "network_error",
                "type": request_type,
                "attempt": attempt,
                "model": model,
                "error": str(exc)[:500],
            })
            if attempt <= retry:
                time.sleep(1.2)
                continue
            raise RuntimeError(f"{request_type}网络请求失败：{exc}") from exc

        except Exception as exc:
            last_error = exc
            raise

    raise RuntimeError(f"{request_type}请求失败：{last_error}")


def _thinking_payload(thinking_type: Optional[str]) -> Dict[str, str] | None:
    if thinking_type in {"enabled", "disabled", "auto"}:
        return {"type": thinking_type}
    return None


def call_text_model(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 12000,
    request_timeout: Optional[int] = None,
    thinking_type: str = "enabled",
) -> str:
    payload: Dict[str, Any] = {
        "model": get_text_model_id(),
        "messages": [
            {"role": "system", "content": "你是一个严谨、实用的 TikTok 女装内容策划和视频提示词生成助手。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    thinking = _thinking_payload(thinking_type)
    if thinking:
        payload["thinking"] = thinking

    return _post_chat(
        payload,
        "文本生成",
        timeout_seconds=request_timeout or get_generation_timeout_seconds(),
        retry=1,
    )


def call_vision_model(
    prompt: str,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    temperature: float = 0.1,
    max_tokens: int = 700,
    request_timeout: Optional[int] = None,
    thinking_type: str = "disabled",
) -> str:
    primary_mode = get_image_input_mode()
    fallback_mode = "raw_base64" if primary_mode == "data_url" else "data_url"
    errors: List[str] = []

    for idx, mode in enumerate([primary_mode, fallback_mode]):
        image_payload = _encode_image(image_bytes, mime_type, mode)
        payload: Dict[str, Any] = {
            "model": get_vision_model_id(),
            "messages": [
                {
                    "role": "system",
                    "content": "你只做服装图片的快速视觉识别。只基于图片可见信息回答，不要长篇推理，不要创意策划。",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_payload}},
                    ],
                },
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        thinking = _thinking_payload(thinking_type)
        if thinking:
            payload["thinking"] = thinking

        _record_api_event({
            "stage": "vision_payload_ready",
            "type": "图片识别",
            "attempt": idx + 1,
            "mode": mode,
            "bytes": len(image_bytes),
            "model": get_vision_model_id(),
            "thinking": thinking_type,
        })
        print(f"[vision-payload] attempt={idx+1} model={get_vision_model_id()} bytes={len(image_bytes)} mode={mode} thinking={thinking_type}")

        try:
            return _post_chat(
                payload,
                f"图片识别({mode})",
                timeout_seconds=request_timeout or get_asset_timeout_seconds(),
                retry=0,
            )
        except RuntimeError as exc:
            msg = str(exc)
            errors.append(f"{mode}: {msg}")
            # retry fallback only for request format errors, not for timeout
            if "超时" in msg:
                break
            if idx == 0 and any(k in msg.lower() for k in ["image", "base64", "url", "content", "400", "invalid", "unsupported"]):
                continue
            break

    raise RuntimeError("图片识别失败。已尝试格式：\n" + "\n".join(errors))
