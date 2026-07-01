from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from PIL import Image
from typing import Any, Dict, List

import streamlit as st
from dotenv import load_dotenv

from config import (
    CAMERA_LANGUAGE,
    CAPTION_STYLES,
    CONFLICTS,
    CONTENT_CATEGORIES,
    CTA_STYLES,
    DEDUP_LEVELS,
    DEFAULTS,
    EMOTIONAL_STYLES,
    OUTPUT_COUNTS,
    OUTPUT_FORMATS,
    PERSONAS,
    RELATIONSHIPS,
    SCRIPT_TYPES,
    SHOT_STRUCTURES,
    STABILITY_MODES,
    VIDEO_GOALS,
    VOICEOVER_STYLES,
)
from prompts import CLOTHING_PROFILE_PROMPT, build_asset_card_prompt, build_auto_recommend_prompt, build_scene_plan_prompt, build_video_prompt
from volc_api import call_text_model, call_vision_model, get_api_status, get_secret

load_dotenv()

st.set_page_config(
    page_title="TikTok Fashion Prompt Studio",
    page_icon="👗",
    layout="wide",
)

APP_CSS = """
<style>
:root {
  --brand: #ff3b5f;
  --brand-dark: #de2448;
  --ink: #101828;
  --muted: #667085;
  --line: #e5e7eb;
  --panel: #ffffff;
  --soft: #f8fafc;
}
.stApp { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 26%, #f8fafc 100%); }
.block-container { padding-top: 1.35rem; max-width: 1500px; }
[data-testid="stHeader"] { background: rgba(248,250,252,.82); backdrop-filter: blur(14px); }
.main-title {
  font-size: 38px; font-weight: 850; letter-spacing: -0.04em; color: var(--ink); margin-bottom: 2px;
}
.sub-title { color: var(--muted); font-size: 14px; margin-bottom: 18px; }
.hero-card {
  border: 1px solid var(--line); border-radius: 18px; padding: 18px 20px;
  background: rgba(255,255,255,.9); box-shadow: 0 14px 40px rgba(16,24,40,.06);
  margin-bottom: 18px;
}
.metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; }
.metric-card {
  border: 1px solid #edf0f5; border-radius: 16px; padding: 14px 16px;
  background: linear-gradient(180deg,#fff,#fbfcff); box-shadow: 0 8px 22px rgba(16,24,40,.04);
}
.metric-label { color: var(--muted); font-size: 12px; margin-bottom: 4px; }
.metric-value { color: var(--ink); font-weight: 750; font-size: 15px; }
.section-note {
  color: #475467; background: #f3f6fb; border: 1px solid #e8edf5; border-radius: 12px;
  padding: 10px 12px; font-size: 13px; margin-bottom: 12px;
}
.stButton > button {
  border-radius: 12px !important; height: 42px; font-weight: 650 !important;
}
.stDownloadButton > button { border-radius: 12px !important; height: 42px; }
[data-baseweb="tag"] {
  background-color: #fff0f3 !important; color: #c9183a !important; border: 1px solid #ffd3dc !important;
  border-radius: 999px !important; font-weight: 650 !important;
}
.stMultiSelect [data-baseweb="select"], .stSelectbox [data-baseweb="select"], .stTextInput input, .stTextArea textarea {
  border-radius: 12px !important;
}
div[data-testid="stExpander"] {
  border: 1px solid #e8edf5 !important; border-radius: 16px !important; background: #fff !important;
  box-shadow: 0 8px 22px rgba(16,24,40,.035);
}
.small-muted { color: var(--muted); font-size: 12px; }
.warning-soft { background:#fff8e6; border:1px solid #ffe6a3; border-radius:12px; padding:10px 12px; color:#7a4b00; font-size:13px; }
.result-box { border:1px solid var(--line); border-radius:16px; padding:16px; background:#fff; }

.api-grid { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap:12px; margin: 8px 0 12px; }
.api-card { border:1px solid #e8edf5; border-radius:16px; padding:14px 16px; background:linear-gradient(180deg,#ffffff,#f8fbff); box-shadow:0 8px 22px rgba(16,24,40,.04); }
.api-k { color:#667085; font-size:12px; margin-bottom:5px; }
.api-v { color:#101828; font-size:13px; font-weight:720; word-break: break-all; }


.api-shell {
  display:grid; grid-template-columns: 190px 1fr; gap:18px;
  border:1px solid #e8edf5; border-radius:22px; background:rgba(255,255,255,.96);
  box-shadow:0 18px 50px rgba(16,24,40,.08); padding:18px; margin-bottom:14px;
}
.api-side { border-right:1px solid #edf0f5; padding-right:14px; }
.api-side-title { font-weight:820; font-size:16px; color:#101828; margin-bottom:12px; }
.api-side-item { border-radius:12px; padding:10px 12px; margin:6px 0; color:#475467; font-size:14px; }
.api-side-item-active { background:#f2f6ff; color:#155eef; font-weight:760; }
.api-main-title { font-size:18px; font-weight:820; color:#101828; margin-bottom:4px; }
.api-main-sub { font-size:13px; color:#667085; margin-bottom:14px; }
.api-status-dot-ok { display:inline-block; width:8px; height:8px; border-radius:999px; background:#12b76a; margin-right:6px; }
.api-status-dot-bad { display:inline-block; width:8px; height:8px; border-radius:999px; background:#f04438; margin-right:6px; }


.block-container { padding-top: 2rem; }
.stButton > button {
  border-radius: 14px !important;
  font-weight: 760 !important;
}
div[data-testid="stExpander"] {
  border-radius: 16px !important;
  border: 1px solid #e7ebf3 !important;
  box-shadow: 0 10px 28px rgba(16,24,40,.035);
}

</style>
"""

SCRIPT_GROUP_RULES = {
    "单人试穿展示": ["单人试穿类"],
    "GRWM 出门前穿搭": ["GRWM 场景类"],
    "POV 原生剧情": ["POV 剧情类"],
    "路人夸赞/路人询问": ["路人夸赞类"],
    "闺蜜/室友/男友反应": ["反应类"],
    "gay bestie styling reaction": ["反应类"],
    "开箱试穿": ["单人试穿类"],
    "Fit Test 服装测试": ["Fit Test 测试类"],
    "Before/After 反差": ["Before / After 反差类"],
    "一衣多穿": ["一衣多穿类"],
    "场景穿搭": ["GRWM 场景类", "一衣多穿类", "POV 剧情类"],
    "街拍采访": ["路人夸赞类"],
    "评论区回复": ["评论区驱动类"],
    "痛点解决": ["痛点解决类", "Fit Test 测试类"],
    "搞笑反差": ["Before / After 反差类", "POV 剧情类"],
    "情绪价值": ["情绪价值类"],
    "伪偷拍/伪纪录片": ["POV 剧情类", "路人夸赞类"],
    "TikTok Shop 软转化": ["TikTok Shop 软转化类", "Fit Test 测试类", "评论区驱动类"],
}


def apply_css() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)


def check_password() -> bool:
    app_password = get_secret("APP_PASSWORD")
    if not app_password:
        st.warning("当前没有设置 APP_PASSWORD。部署到公网前，请在 Streamlit Secrets 里设置登录密码。")
        return True
    if st.session_state.get("authenticated") is True:
        return True
    st.markdown('<div class="main-title">TikTok Fashion Prompt Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">请输入访问密码后使用。</div>', unsafe_allow_html=True)
    with st.form("login_form"):
        password = st.text_input("访问密码", type="password")
        submitted = st.form_submit_button("进入", use_container_width=True)
    if submitted:
        if password == app_password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密码错误。")
    return False


def init_state() -> None:
    defaults = {
        "clothing_profile": "",
        "auto_recommendation": "",
        "generation_result": "",
        "scene_plan": "",
        "last_uploaded_name": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_mime_type(file_name: str) -> str:
    lower = file_name.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"



def compress_image_for_api(image_bytes: bytes, max_mb: float = 2.0) -> tuple[bytes, str, str]:
    """Compress uploaded image for API stability.

    Returns: (image_bytes, mime_type, note)
    """
    original_mb = len(image_bytes) / 1024 / 1024
    if original_mb <= max_mb:
        return image_bytes, "image/jpeg", f"原图 {original_mb:.1f}MB，未压缩。"

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    max_side = 1600
    img.thumbnail((max_side, max_side))

    quality = 88
    best = None
    while quality >= 55:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        best = data
        if len(data) / 1024 / 1024 <= max_mb:
            break
        quality -= 8

    new_mb = len(best) / 1024 / 1024
    note = f"原图 {original_mb:.1f}MB，已自动压缩为 {new_mb:.1f}MB 后再调用图片理解模型。"
    return best, "image/jpeg", note



def flatten_script_types(groups: List[str] | None = None) -> List[str]:
    result: List[str] = []
    allowed = set(groups or SCRIPT_TYPES.keys())
    for group, items in SCRIPT_TYPES.items():
        if group in allowed:
            result.extend([f"{group} / {item}" for item in items])
    return result


def compatible_script_groups(content_categories: List[str]) -> List[str]:
    groups: List[str] = []
    for category in content_categories:
        groups.extend(SCRIPT_GROUP_RULES.get(category, []))
    if not groups:
        return list(SCRIPT_TYPES.keys())
    # keep order, remove duplicates
    seen = set()
    ordered = []
    for group in groups:
        if group not in seen:
            ordered.append(group)
            seen.add(group)
    return ordered


def settings_to_text(settings: Dict[str, Any]) -> str:
    lines = []
    for key, value in settings.items():
        if isinstance(value, list):
            value_text = ", ".join(map(str, value)) if value else "未选择 / 让 AI 自动判断"
        else:
            value_text = str(value)
        lines.append(f"{key}: {value_text}")
    return "\n".join(lines)


def safe_index(options: List[Any], value: Any, fallback: int = 0) -> int:
    try:
        return options.index(value)
    except ValueError:
        return fallback


def safe_defaults(options: List[Any], defaults: List[Any]) -> List[Any]:
    return [item for item in defaults if item in options]


def parse_videos_to_rows(markdown_text: str) -> List[Dict[str, str]]:
    blocks = re.split(r"(?=###\s*Video\s*\d+|【视频编号】)", markdown_text, flags=re.IGNORECASE)
    rows: List[Dict[str, str]] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        direction_match = re.search(r"(?:Direction|【视频方向】)[:：]?\s*\n?(.+)", block)
        hook_match = re.search(r"(?:Hook|【3秒 Hook】)[:：]?\s*\n?(.+)", block)
        rows.append(
            {
                "index": str(len(rows) + 1),
                "video_direction": direction_match.group(1).strip() if direction_match else "",
                "hook": hook_match.group(1).strip() if hook_match else "",
                "full_text": block,
            }
        )
    if not rows and markdown_text.strip():
        rows.append({"index": "1", "video_direction": "", "hook": "", "full_text": markdown_text.strip()})
    return rows


def rows_to_csv_text(rows: List[Dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["index", "video_direction", "hook", "full_text"])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_header() -> None:
    st.markdown('<div class="main-title">TikTok Fashion Prompt Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">美区女装原生视频提示词工作台 · 稳定款式识别 · 场景规划 · 文本提示词输出</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-card">
          <div class="metric-grid">
            <div class="metric-card"><div class="metric-label">模型接入</div><div class="metric-value">Seed 2.1 Pro</div></div>
            <div class="metric-card"><div class="metric-label">场景逻辑</div><div class="metric-value">先规划 / 再生成</div></div>
            <div class="metric-card"><div class="metric-label">输出格式</div><div class="metric-value">15秒 9:16 Seedance Prompt</div></div>
            <div class="metric-card"><div class="metric-label">冲突控制</div><div class="metric-value">资产卡兼容过滤</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_api_center() -> None:
    status = get_api_status()
    api_key_status = status.get("api_key_configured", "未配置")
    base_url = status.get("base_url", "")
    text_model = status.get("text_model", "未配置")
    vision_model = status.get("vision_model", "未配置")
    image_input_mode = status.get("image_input_mode", "data_url")
    request_timeout = status.get("request_timeout", "180")
    asset_timeout_status = status.get("asset_timeout", "120")
    generation_timeout_status = status.get("generation_timeout", "240")
    is_configured = api_key_status == "已配置" and text_model != "未配置"

    with st.expander("模型接入中心 · Seed 2.1 Pro", expanded=not is_configured):
        st.markdown(
            """
            <div class="api-shell">
              <div class="api-side">
                <div class="api-side-title">设置</div>
                <div class="api-side-item api-side-item-active">🔑 连接配置</div>
                <div class="api-side-item">⚙️ 能力路由</div>
                <div class="api-side-item">🧪 连接状态</div>
                <div class="api-side-item">🛡️ 安全配置</div>
              </div>
              <div>
                <div class="api-main-title">Seed 2.1 Pro 接入</div>
                <div class="api-main-sub">已预填你的 Seed 2.1 Pro Endpoint：ep-20260625032114-7d4xz。API Key 仍需在页面或 Streamlit Secrets 中填写。</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        key_dot = '<span class="api-status-dot-ok"></span>' if api_key_status == "已配置" else '<span class="api-status-dot-bad"></span>'
        st.markdown(
            f"""
            <div class="api-grid">
              <div class="api-card"><div class="api-k">API Key</div><div class="api-v">{key_dot}{api_key_status}</div></div>
              <div class="api-card"><div class="api-k">Base URL</div><div class="api-v">{base_url}</div></div>
              <div class="api-card"><div class="api-k">Text Model</div><div class="api-v">{text_model}</div></div>
              <div class="api-card"><div class="api-k">Vision Model</div><div class="api-v">{vision_model}</div></div>
              <div class="api-card"><div class="api-k">Image Mode</div><div class="api-v">{image_input_mode}</div></div>
              <div class="api-card"><div class="api-k">Default Timeout</div><div class="api-v">{request_timeout}s</div></div>
              <div class="api-card"><div class="api-k">Asset Timeout</div><div class="api-v">{asset_timeout_status}s</div></div>
              <div class="api-card"><div class="api-k">Generation Timeout</div><div class="api-v">{generation_timeout_status}s</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )



        mode = st.radio(
            "配置方式",
            ["页面配置", "后台长期配置"],
            horizontal=True,
            index=0,
            help="页面配置用于快速接入；正式长期使用建议保存到后台配置。",
        )

        if mode == "页面配置":
            current = st.session_state.get("runtime_api_config", {})
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox(
                    "服务商类型",
                    ["Seed 2.1 Pro", "OpenAI 兼容接口"],
                    index=0,
                )
                base_url_input = st.text_input(
                    "API URL",
                    value=current.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
                    placeholder="https://ark.cn-beijing.volces.com/api/v3",
                )
                api_key_input = st.text_input(
                    "API Key",
                    value=current.get("ARK_API_KEY", ""),
                    type="password",
                    placeholder="粘贴你的 API Key",
                )
            with col2:
                model_mode = st.selectbox(
                    "能力路由",
                    ["单模型：Seed 2.1 Pro 同时处理文本和图片", "双模型：文本 / 图片分开配置"],
                    index=0,
                )
                seed_model = st.text_input(
                    "Doubao Seed 2.1 Pro 模型 ID / Endpoint ID",
                    value=current.get("DOUBAO_SEED21_PRO_MODEL_ID", "ep-20260625032114-7d4xz"),
                    placeholder="ep-20260625032114-7d4xz",
                )
                image_input_mode = st.selectbox(
                    "图片编码格式",
                    ["data_url", "raw_base64"],
                    index=0 if current.get("ARK_IMAGE_INPUT_MODE", "data_url") == "data_url" else 1,
                    help="默认 data_url；若格式不兼容，系统会尝试备用格式。",
                )
                request_timeout = st.selectbox(
                    "默认请求等待时间",
                    [60, 90, 120, 180, 240, 300],
                    index=[60, 90, 120, 180, 240, 300].index(int(current.get("ARK_REQUEST_TIMEOUT", "180"))) if str(current.get("ARK_REQUEST_TIMEOUT", "180")).isdigit() and int(current.get("ARK_REQUEST_TIMEOUT", "180")) in [60, 90, 120, 180, 240, 300] else 3,
                    help="通用兜底等待时间。",
                )
                asset_timeout = st.selectbox(
                    "资产识别等待时间",
                    [60, 90, 120, 180],
                    index=[60, 90, 120, 180].index(int(current.get("ARK_ASSET_TIMEOUT", "120"))) if str(current.get("ARK_ASSET_TIMEOUT", "120")).isdigit() and int(current.get("ARK_ASSET_TIMEOUT", "120")) in [60, 90, 120, 180] else 2,
                    help="资产识别不做深度思考，建议 120 秒。",
                )
                generation_timeout = st.selectbox(
                    "提示词生成等待时间",
                    [120, 180, 240, 300],
                    index=[120, 180, 240, 300].index(int(current.get("ARK_GENERATION_TIMEOUT", "240"))) if str(current.get("ARK_GENERATION_TIMEOUT", "240")).isdigit() and int(current.get("ARK_GENERATION_TIMEOUT", "240")) in [120, 180, 240, 300] else 2,
                    help="场景规划和提示词生成会做深度规划，建议 240 秒。",
                )
                if model_mode == "双模型：文本 / 图片分开配置":
                    text_model_input = st.text_input("文本生成模型 ID / Endpoint ID", value=current.get("ARK_TEXT_MODEL_ID", ""))
                    vision_model_input = st.text_input("图片理解模型 ID / Endpoint ID", value=current.get("ARK_VISION_MODEL_ID", ""))
                else:
                    text_model_input = ""
                    vision_model_input = ""

            c1, c2, _ = st.columns([1, 1, 2])
            with c1:
                if st.button("保存配置", use_container_width=True):
                    runtime_config = {
                        "ARK_API_KEY": api_key_input.strip(),
                        "ARK_BASE_URL": base_url_input.strip() or "https://ark.cn-beijing.volces.com/api/v3",
                        "DOUBAO_SEED21_PRO_MODEL_ID": seed_model.strip(),
                        "ARK_IMAGE_INPUT_MODE": image_input_mode,
                        "ARK_REQUEST_TIMEOUT": str(request_timeout),
                        "ARK_ASSET_TIMEOUT": str(asset_timeout),
                        "ARK_GENERATION_TIMEOUT": str(generation_timeout),
                    }
                    if text_model_input.strip():
                        runtime_config["ARK_TEXT_MODEL_ID"] = text_model_input.strip()
                    if vision_model_input.strip():
                        runtime_config["ARK_VISION_MODEL_ID"] = vision_model_input.strip()
                    st.session_state["runtime_api_config"] = runtime_config
                    st.success("已保存配置。现在可以直接测试图片分析和提示词生成。")
                    st.rerun()
            with c2:
                if st.button("清空配置", use_container_width=True):
                    st.session_state["runtime_api_config"] = {}
                    st.warning("已清空当前会话 连接配置。")
                    st.rerun()

            asset_timeout = locals().get("asset_timeout", int(current.get("ARK_ASSET_TIMEOUT", "120")) if str(current.get("ARK_ASSET_TIMEOUT", "120")).isdigit() else 120)
            generation_timeout = locals().get("generation_timeout", int(current.get("ARK_GENERATION_TIMEOUT", "240")) if str(current.get("ARK_GENERATION_TIMEOUT", "240")).isdigit() else 240)

            secrets_text = f"""ARK_API_KEY = "你的 API Key"
ARK_BASE_URL = "{base_url_input.strip() or 'https://ark.cn-beijing.volces.com/api/v3'}"
DOUBAO_SEED21_PRO_MODEL_ID = "{seed_model.strip() or '你的豆包 Seed 2.1 Pro 模型ID或Endpoint ID'}"
ARK_IMAGE_INPUT_MODE = "{image_input_mode}"
ARK_REQUEST_TIMEOUT = "{request_timeout}"
ARK_ASSET_TIMEOUT = "{asset_timeout}"
ARK_GENERATION_TIMEOUT = "{generation_timeout}"
APP_PASSWORD = "你设置的网页访问密码" """
            if text_model_input.strip() or vision_model_input.strip():
                secrets_text += f"""

# 可选：文本和图片分开配置
ARK_TEXT_MODEL_ID = "{text_model_input.strip() or '文本生成模型ID或Endpoint ID'}"
ARK_VISION_MODEL_ID = "{vision_model_input.strip() or '图片理解模型ID或Endpoint ID'}" """
            st.markdown("<div class='section-note'>复制下面内容到后台配置，可长期保存。为安全起见，这里不会回显真实 API Key。</div>", unsafe_allow_html=True)
            st.code(secrets_text, language="toml")

        else:
            st.markdown(
                "<div class='section-note'>长期使用请在后台配置中填写，不要把密钥写进 GitHub 文件。</div>",
                unsafe_allow_html=True,
            )
            st.code(
                """ARK_API_KEY = "你的 API Key"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_SEED21_PRO_MODEL_ID = "你的豆包 Seed 2.1 Pro 模型ID或Endpoint ID"
ARK_IMAGE_INPUT_MODE = "data_url"
ARK_REQUEST_TIMEOUT = "180"
ARK_ASSET_TIMEOUT = "120"
ARK_GENERATION_TIMEOUT = "240"
APP_PASSWORD = "你设置的网页访问密码"

# 可选：如果文本和图片用不同模型
# ARK_TEXT_MODEL_ID = "文本生成模型ID或Endpoint ID"
# ARK_VISION_MODEL_ID = "图片理解模型ID或Endpoint ID" """,
                language="toml",
            )
            st.markdown(
                "<div class='section-note'>后台配置路径：Streamlit Cloud → App → Settings → Secrets → 粘贴配置 → Save → Reboot app。</div>",
                unsafe_allow_html=True,
            )


def render_left_panel() -> None:
    st.subheader("1. 上传参考图")
    uploaded_file = st.file_uploader("上传 jpg / jpeg / png / webp", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

    if uploaded_file is not None:
        st.session_state.last_uploaded_name = uploaded_file.name
        image_bytes = uploaded_file.getvalue()
        file_size_mb = len(image_bytes) / 1024 / 1024
        st.markdown(
            f"<div class='section-note'>已上传：<b>{uploaded_file.name}</b> · {file_size_mb:.1f} MB。页面不展示大图，保持工作台清爽。</div>",
            unsafe_allow_html=True,
        )

        if st.button("生成款式资产卡", type="primary", use_container_width=True):
            try:
                with st.spinner("正在提取服装可见结构..."):
                    api_image_bytes, mime_type, compress_note = compress_image_for_api(image_bytes, max_mb=2.0)
                    vision_brief = call_vision_model(
                        CLOTHING_PROFILE_PROMPT,
                        image_bytes=api_image_bytes,
                        mime_type=mime_type,
                        temperature=0.1,
                        max_tokens=700,
                        request_timeout=120,
                        thinking_type="disabled",
                    )

                if not vision_brief or not vision_brief.strip():
                    st.error("款式识别未返回有效内容，请换一张更清晰的参考图后重试。")
                    return

                with st.spinner("正在整理款式资产卡..."):
                    asset_prompt = build_asset_card_prompt(vision_brief)
                    asset_card = call_text_model(asset_prompt, temperature=0.2, max_tokens=1800, request_timeout=120, thinking_type="disabled")

                if asset_card and asset_card.strip():
                    st.session_state.clothing_profile = asset_card
                    st.session_state.clothing_profile_editor = asset_card
                    st.success("款式资产卡已生成")
                else:
                    st.session_state.clothing_profile = vision_brief
                    st.session_state.clothing_profile_editor = vision_brief
                    st.warning("已生成基础识别结果，正式资产卡整理未返回。")

            except Exception as exc:
                st.error(f"款式识别失败：{exc}")
                st.markdown(
                    "<div class='warning-soft'>建议检查：API Key、模型 ID、图片识别能力、图片清晰度。正式使用建议上传 1–3MB 的清晰参考图。</div>",
                    unsafe_allow_html=True,
                )

        with st.expander("高级诊断", expanded=False):
            st.caption("仅用于排查接口链路。正式使用时无需打开。")
            st.json(st.session_state.get("last_api_event", {"status": "暂无请求记录"}))

    st.subheader("2. 款式资产卡")
    st.markdown("<div class='section-note'>系统会提取版型、结构、面料视觉、可展示卖点；默认不描述颜色。</div>", unsafe_allow_html=True)

    if "clothing_profile_editor" not in st.session_state:
        st.session_state.clothing_profile_editor = st.session_state.clothing_profile

    clothing_profile_input = st.text_area(
        "可手动修正 AI 看错的地方",
        height=420,
        key="clothing_profile_editor",
    )
    st.session_state.clothing_profile = clothing_profile_input
    if st.session_state.clothing_profile.strip():
        st.caption(f"已载入资产卡内容：{len(st.session_state.clothing_profile)} 字")

    if st.button("AI 自动推荐创意策略", use_container_width=True, disabled=not bool(st.session_state.clothing_profile.strip())):
        with st.spinner("正在根据款式资产卡推荐策略... "):
            try:
                prompt = build_auto_recommend_prompt(st.session_state.clothing_profile)
                st.session_state.auto_recommendation = call_text_model(prompt, temperature=0.5, max_tokens=5000, request_timeout=240, thinking_type="enabled")
                st.success("推荐策略已生成")
            except Exception as exc:
                st.error(f"自动推荐失败：{exc}")

    if st.session_state.auto_recommendation:
        with st.expander("查看 AI 自动推荐策略", expanded=False):
            st.markdown(st.session_state.auto_recommendation)


def render_settings_panel() -> Dict[str, Any]:
    st.subheader("3. 视频生成控制台")

    with st.expander("基础设置", expanded=True):
        video_goals = st.multiselect("视频目标", VIDEO_GOALS, default=safe_defaults(VIDEO_GOALS, DEFAULTS.get("video_goals", [])))
        output_count = st.selectbox("输出数量", OUTPUT_COUNTS, index=safe_index(OUTPUT_COUNTS, DEFAULTS.get("output_count", OUTPUT_COUNTS[0])))
        output_format = st.selectbox("输出格式", OUTPUT_FORMATS, index=safe_index(OUTPUT_FORMATS, DEFAULTS.get("output_format", OUTPUT_FORMATS[0])))
        color_variants = st.text_input(
            "颜色变体（可选）",
            value="",
            placeholder="例如：black, cream, pink, brown。留空则不强调颜色。",
            help="资产分析不会识别/描述颜色。多个颜色一起生成时，在这里填写。",
        )

    with st.expander("创意方向", expanded=True):
        creative_mode = st.selectbox(
            "创意生成模式",
            ["AI全自动随机（推荐）", "半自动：只指定内容大类", "手动：内容大类 + 细分脚本"],
            index=0,
            help="推荐用全自动随机。系统会在内容大类、细分脚本、剧情冲突之间做冲突过滤。",
        )

        if creative_mode == "AI全自动随机（推荐）":
            content_categories: List[str] = []
            selected_script_types: List[str] = []
            st.markdown("<div class='section-note'>当前为随机模式：AI 会先为本批视频深度规划不同真实场景，再根据资产卡过滤不兼容的人群、卖点和内容类型。</div>", unsafe_allow_html=True)
        else:
            content_categories = st.multiselect(
                "内容大类",
                CONTENT_CATEGORIES,
                default=safe_defaults(CONTENT_CATEGORIES, DEFAULTS.get("content_categories", [])),
            )
            if creative_mode == "手动：内容大类 + 细分脚本":
                groups = compatible_script_groups(content_categories)
                selected_script_types = st.multiselect(
                    "细分脚本类型（已按内容大类过滤）",
                    flatten_script_types(groups),
                    default=[],
                    help="这里只显示和上方内容大类兼容的脚本，减少冲突。",
                )
            else:
                selected_script_types = []
                st.markdown("<div class='section-note'>细分脚本由 AI 自动匹配，只按你选择的内容大类生成。</div>", unsafe_allow_html=True)

        conflict_mode = st.selectbox(
            "剧情冲突模式",
            ["AI随机生成大量冲突（推荐）", "手动选择冲突", "不强调冲突"],
            index=0,
        )
        if conflict_mode == "手动选择冲突":
            conflicts = st.multiselect("剧情冲突", CONFLICTS, default=[])
        else:
            conflicts = []

        st.markdown("<div class='section-note'>服装卖点重点不再手动全选。系统会从款式资产卡自动提取，例如版型、腰线、领口、褶皱、裙摆、面料流动感等。</div>", unsafe_allow_html=True)

    with st.expander("人物与场景", expanded=False):
        use_reference_person = st.checkbox("默认使用参考图人物，不额外指定人设", value=True)
        if use_reference_person:
            personas: List[str] = []
            st.markdown("<div class='section-note'>已禁止默认人设。生成时以参考图人物作为主体，不强行改成 college girl / office woman 等。</div>", unsafe_allow_html=True)
        else:
            personas = st.multiselect("人物人设", PERSONAS, default=[])

        relationship_mode = st.selectbox(
            "人物关系模式",
            ["AI随机覆盖完整人物关系池（推荐）", "只用单人", "手动选择人物关系"],
            index=0,
        )
        if relationship_mode == "手动选择人物关系":
            relationships = st.multiselect("人物关系", RELATIONSHIPS, default=[])
        elif relationship_mode == "只用单人":
            relationships = ["单人自拍"]
        else:
            relationships = []
            with st.expander("查看完整人物关系池", expanded=False):
                st.write("、".join(RELATIONSHIPS))

        scene_mode = st.selectbox(
            "场景模式",
            ["AI随机生成欧美真实生活场景（推荐）", "指定场景方向", "固定自定义场景"],
            index=0,
        )
        if scene_mode == "指定场景方向":
            scene_direction = st.text_input("场景方向", placeholder="例如：laundry room / coffee shop / parking lot / college campus / suburban house")
        elif scene_mode == "固定自定义场景":
            scene_direction = st.text_area("固定场景描述", height=100, placeholder="写你想固定使用的场景描述。")
        else:
            scene_direction = "AI 每次生成前先做场景深度规划：从大生活分类进入，再深挖具体场所、装修、布局、物件、光线、声音、动作，不使用固定死场景库。"

    with st.expander("拍摄控制", expanded=False):
        shot_structure = st.selectbox(
            "拍摄结构",
            SHOT_STRUCTURES,
            index=safe_index(SHOT_STRUCTURES, DEFAULTS.get("shot_structure", SHOT_STRUCTURES[0])),
        )
        camera_language = st.multiselect(
            "镜头语言",
            CAMERA_LANGUAGE,
            default=safe_defaults(CAMERA_LANGUAGE, DEFAULTS.get("camera_language", [])),
        )
        stability_mode = st.selectbox(
            "AI 稳定性",
            STABILITY_MODES,
            index=safe_index(STABILITY_MODES, DEFAULTS.get("stability_mode", STABILITY_MODES[0])),
        )
        st.markdown("<div class='section-note'>如果生成多人互动，系统默认限制 2 人以内，避免 Seedance 人物错乱。</div>", unsafe_allow_html=True)

    with st.expander("语言与转化", expanded=False):
        emotional_styles = st.multiselect("情绪风格", EMOTIONAL_STYLES, default=safe_defaults(EMOTIONAL_STYLES, DEFAULTS.get("emotional_styles", [])))
        voiceover_style = st.multiselect("口播风格", VOICEOVER_STYLES, default=safe_defaults(VOICEOVER_STYLES, DEFAULTS.get("voiceover_style", [])))
        caption_style = st.multiselect("字幕风格", CAPTION_STYLES, default=safe_defaults(CAPTION_STYLES, DEFAULTS.get("caption_style", [])))
        cta_style = st.selectbox("CTA 风格", CTA_STYLES, index=safe_index(CTA_STYLES, DEFAULTS.get("cta_style", CTA_STYLES[0])))

    with st.expander("高级设置", expanded=False):
        dedup_level = st.selectbox("创意去重强度", DEDUP_LEVELS, index=safe_index(DEDUP_LEVELS, DEFAULTS.get("dedup_level", DEDUP_LEVELS[-1])))
        allow_auto_recommend = st.checkbox("允许 AI 自动推荐未选择项", value=True)
        conflict_filter = st.checkbox("启用内容冲突过滤", value=True)
        exclude_low_stability = st.checkbox("排除低稳定脚本", value=True)
        prioritize_clothing_details = st.checkbox("优先突出服装纹理和款式细节", value=True)
        avoid_hard_ads = st.checkbox("CTA 根据目标自动判断，避免无脑硬广", value=True)
        use_us_tiktok_slang = st.checkbox("生成美国 TikTok 口语", value=True)
        use_scene_planner = st.checkbox("每次生成前先进行场景深度规划", value=True)

    relationship_pool_text = "、".join(RELATIONSHIPS)
    conflict_pool_text = "、".join(CONFLICTS)

    return {
        "视频目标": video_goals,
        "输出数量": output_count,
        "输出格式": output_format,
        "颜色变体": color_variants if color_variants.strip() else "未填写，不强调颜色",
        "创意生成模式": creative_mode,
        "内容大类": content_categories if content_categories else "AI全自动随机，覆盖完整内容大类库",
        "细分脚本类型": selected_script_types if selected_script_types else "AI自动匹配兼容细分脚本，不硬拼冲突组合",
        "剧情冲突模式": conflict_mode,
        "剧情冲突": conflicts if conflicts else f"AI从大型冲突池随机生成并过滤冲突；可用冲突池包括：{conflict_pool_text}",
        "服装卖点重点": "从款式资产卡自动提取，不使用固定卖点全选",
        "人物人设": "默认禁止额外指定人设，使用参考图人物" if use_reference_person else personas,
        "人物关系模式": relationship_mode,
        "人物关系": relationships if relationships else f"AI从完整人物关系池随机覆盖；可用关系池包括：{relationship_pool_text}",
        "场景模式": scene_mode,
        "拍摄场景": scene_direction,
        "拍摄结构": shot_structure,
        "镜头语言": camera_language,
        "AI 稳定性": stability_mode,
        "情绪风格": emotional_styles,
        "口播风格": voiceover_style if voiceover_style else "自动判断",
        "字幕风格": caption_style if caption_style else "不要字幕",
        "CTA 风格": cta_style,
        "创意去重强度": dedup_level,
        "允许 AI 自动推荐未选择项": allow_auto_recommend,
        "启用内容冲突过滤": conflict_filter,
        "排除低稳定脚本": exclude_low_stability,
        "优先突出服装纹理和款式细节": prioritize_clothing_details,
        "CTA 根据目标自动判断，避免无脑硬广": avoid_hard_ads,
        "生成美国 TikTok 口语": use_us_tiktok_slang,
        "每次生成前先进行场景深度规划": use_scene_planner,
    }


def render_generation(settings: Dict[str, Any]) -> None:
    st.subheader("4. 生成结果")
    st.markdown("<div class='section-note'>本工具只输出 Seedance 2.0 文本提示词，不生成图片或视频。生成阶段会进行深度规划，页面会显示当前进度。</div>", unsafe_allow_html=True)
    if st.button("生成 Seedance 2.0 文本提示词", type="primary", use_container_width=True, disabled=not bool(st.session_state.clothing_profile.strip())):
        progress = st.container()
        with progress:
            step_scene = st.empty()
            step_filter = st.empty()
            step_prompt = st.empty()

        try:
            user_settings = settings_to_text(settings)

            if settings.get("每次生成前先进行场景深度规划", True):
                step_scene.info("思考中：正在规划本批真实欧美生活场景，避免场景重复。")
                scene_prompt = build_scene_plan_prompt(st.session_state.clothing_profile, user_settings)
                with st.spinner("思考中：正在做场景深度规划..."):
                    st.session_state.scene_plan = call_text_model(
                        scene_prompt,
                        temperature=1.15,
                        max_tokens=12000,
                        request_timeout=240,
                        thinking_type="enabled",
                    )
                step_scene.success("场景规划完成")
            else:
                st.session_state.scene_plan = "未启用场景深度规划。"
                step_scene.info("已跳过场景深度规划")

            step_filter.info("思考中：正在进行资产卡兼容性判断，过滤不匹配的人群、卖点和脚本结构。")
            prompt = build_video_prompt(st.session_state.clothing_profile, user_settings, st.session_state.scene_plan)
            step_filter.success("兼容性判断完成")

            step_prompt.info("思考中：正在生成 15 秒 9:16 Seedance 2.0 文本提示词。")
            with st.spinner("思考中：正在生成完整提示词..."):
                st.session_state.generation_result = call_text_model(
                    prompt,
                    temperature=0.85,
                    max_tokens=30000,
                    request_timeout=300,
                    thinking_type="enabled",
                )
            step_prompt.success("提示词生成完成")
            st.success("生成完成")

        except Exception as exc:
            st.error(f"生成失败：{exc}")

    if st.session_state.scene_plan:
        with st.expander("查看本批场景深度规划表", expanded=False):
            st.markdown(st.session_state.scene_plan)

    if st.session_state.generation_result:
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown(st.session_state.generation_result)
        st.markdown("</div>", unsafe_allow_html=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_name = f"tiktok_fashion_prompts_{timestamp}.txt"
        csv_name = f"tiktok_fashion_prompts_{timestamp}.csv"
        st.text_area("复制全部结果：点击文本框后 Ctrl+A / Ctrl+C", st.session_state.generation_result, height=260)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button("下载 TXT", data=st.session_state.generation_result.encode("utf-8"), file_name=txt_name, mime="text/plain", use_container_width=True)
        with col2:
            csv_text = rows_to_csv_text(parse_videos_to_rows(st.session_state.generation_result))
            st.download_button("下载 CSV", data=csv_text.encode("utf-8-sig"), file_name=csv_name, mime="text/csv", use_container_width=True)


def main() -> None:
    apply_css()
    if not check_password():
        return
    init_state()
    render_header()
    render_api_center()
    left, right = st.columns([0.38, 0.62], gap="large")
    with left:
        render_left_panel()
    with right:
        settings = render_settings_panel()
        render_generation(settings)


if __name__ == "__main__":
    main()
