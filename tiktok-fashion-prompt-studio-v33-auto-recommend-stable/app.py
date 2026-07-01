from __future__ import annotations

import csv
import io
import re
import hashlib
from datetime import datetime
from PIL import Image
from typing import Any, Dict, List

import streamlit as st

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
from qiniu_image_hosting import has_image_hosting_config, upload_to_qiniu, get_image_hosting_status


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

    hosting_status = get_image_hosting_status()
    qiniu_status = hosting_status.get("image_hosting", "未配置")
    qiniu_bucket = hosting_status.get("bucket", "未配置")
    qiniu_domain = hosting_status.get("domain", "未配置")
    qiniu_scheme = hosting_status.get("scheme", "http")

    is_configured = (
        api_key_status == "已配置"
        and text_model != "未配置"
        and qiniu_status == "已配置"
    )

    with st.expander("模型接入中心 · 后台长期配置", expanded=not is_configured):
        st.markdown(
            """
            <div class="api-shell">
              <div class="api-side">
                <div class="api-side-title">设置</div>
                <div class="api-side-item api-side-item-active">🔐 后台配置</div>
                <div class="api-side-item">🖼️ 图片上传</div>
                <div class="api-side-item">🧠 模型状态</div>
                <div class="api-side-item">🛡️ 安全配置</div>
              </div>
              <div>
                <div class="api-main-title">长期配置模式</div>
                <div class="api-main-sub">配置统一从 Streamlit Secrets 读取。刷新页面、重启 App 后不会丢失；前端不再保存或显示密钥。</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        key_dot = '<span class="api-status-dot-ok"></span>' if api_key_status == "已配置" else '<span class="api-status-dot-bad"></span>'
        qiniu_dot = '<span class="api-status-dot-ok"></span>' if qiniu_status == "已配置" else '<span class="api-status-dot-bad"></span>'

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
              <div class="api-card"><div class="api-k">Qiniu</div><div class="api-v">{qiniu_dot}{qiniu_status}</div></div>
              <div class="api-card"><div class="api-k">Bucket</div><div class="api-v">{qiniu_bucket}</div></div>
              <div class="api-card"><div class="api-k">Image Domain</div><div class="api-v">{qiniu_scheme}://{qiniu_domain}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='section-note'>永久保存请在 Streamlit Cloud 后台 Secrets 中填写配置。页面内不再提供临时输入框，避免刷新丢失和密钥暴露。</div>",
            unsafe_allow_html=True,
        )

        secrets_template = """ARK_API_KEY = "你的火山 API Key"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DOUBAO_SEED21_PRO_MODEL_ID = "ep-20260625032114-7d4xz"

ARK_IMAGE_INPUT_MODE = "data_url"
ARK_REQUEST_TIMEOUT = "180"
ARK_ASSET_TIMEOUT = "120"
ARK_GENERATION_TIMEOUT = "240"

QINIU_ACCESS_KEY = "你的七牛 AccessKey"
QINIU_SECRET_KEY = "你的七牛 SecretKey"
QINIU_BUCKET = "tiktok-fashion-vision-suryus"
QINIU_DOMAIN = "thhne79gp.hd-bkt.clouddn.com"
QINIU_SCHEME = "http"
QINIU_PREFIX = "fashion-uploads"

APP_PASSWORD = "123456"
"""
        st.code(secrets_template, language="toml")

        st.markdown(
            "<div class='section-note'>路径：Streamlit Cloud → 你的 App → Settings → Secrets → 粘贴配置 → Save → Reboot app。</div>",
            unsafe_allow_html=True,
        )

        if not is_configured:
            st.warning("当前后台配置不完整。请先在 Streamlit Secrets 填好火山 API 和七牛云配置，然后 Reboot app。")
        else:
            st.success("后台配置已就绪。可以上传图片并生成款式资产卡。")


def render_left_panel() -> None:
    st.subheader("1. 上传参考图")
    uploaded_file = st.file_uploader("上传 jpg / jpeg / png / webp", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

    if uploaded_file is not None:
        st.session_state.last_uploaded_name = uploaded_file.name
        image_bytes = uploaded_file.getvalue()
        file_size_mb = len(image_bytes) / 1024 / 1024
        image_hash = hashlib.sha1(image_bytes).hexdigest()

        st.markdown(
            f"<div class='section-note'>已上传：<b>{uploaded_file.name}</b> · {file_size_mb:.1f} MB。页面不展示大图，保持工作台清爽。</div>",
            unsafe_allow_html=True,
        )

        # Auto upload to Qiniu when a new image is dropped into the uploader.
        if has_image_hosting_config():
            if st.session_state.get("qiniu_image_hash") != image_hash:
                try:
                    with st.spinner("正在上传参考图，生成图片 URL..."):
                        api_image_bytes, mime_type, compress_note = compress_image_for_api(image_bytes, max_mb=2.0)
                        image_url, qiniu_debug = upload_to_qiniu(
                            api_image_bytes,
                            original_filename=uploaded_file.name or "fashion-reference.jpg",
                            mime_type=mime_type,
                        )
                        st.session_state.qiniu_image_hash = image_hash
                        st.session_state.qiniu_image_url = image_url
                        st.session_state.qiniu_debug = {
                            **qiniu_debug,
                            "compress_note": compress_note,
                        }
                    st.success("参考图已上传，图片 URL 已就绪")
                except Exception as exc:
                    st.session_state.qiniu_image_hash = ""
                    st.session_state.qiniu_image_url = ""
                    st.session_state.qiniu_debug = {"error": str(exc)}
                    st.warning(f"七牛云图片上传失败，将暂时使用小图 Base64 兜底：{exc}")
            else:
                st.success("参考图图片 URL 已就绪")

            with st.expander("图片 URL 状态", expanded=False):
                st.write(st.session_state.get("qiniu_image_url", ""))
                st.json(st.session_state.get("qiniu_debug", {}))
        else:
            st.markdown(
                "<div class='warning-soft'>当前未配置七牛云图片上传。系统会用小图 Base64 兜底，但仍可能不稳定。建议在模型接入中心填写七牛配置。</div>",
                unsafe_allow_html=True,
            )

        if st.button("生成款式资产卡", type="primary", use_container_width=True):
            try:
                with st.spinner("正在提取服装可见结构..."):
                    image_url = st.session_state.get("qiniu_image_url", "")
                    if image_url:
                        vision_brief = call_vision_model(
                            CLOTHING_PROFILE_PROMPT,
                            image_url=image_url,
                            temperature=0.1,
                            max_tokens=700,
                            request_timeout=120,
                            thinking_type="disabled",
                        )
                    else:
                        api_image_bytes, mime_type, compress_note = compress_image_for_api(image_bytes, max_mb=0.35)
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
                    "<div class='warning-soft'>建议检查：API Key、模型 ID、七牛图片 URL 是否能在浏览器打开、图片清晰度。若出现 write timeout，请优先确认七牛上传是否成功。</div>",
                    unsafe_allow_html=True,
                )

        with st.expander("高级诊断", expanded=False):
            st.caption("仅用于排查接口链路。正式使用时无需打开。")
            st.json({
                "api_event": st.session_state.get("last_api_event", {"status": "暂无请求记录"}),
                "image_hosting": get_image_hosting_status(),
                "qiniu_debug": st.session_state.get("qiniu_debug", {}),
            })

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
        progress = st.empty()
        try:
            progress.info("正在快速读取资产卡，筛选适配人群、卖点和拍摄方向...")
            prompt = build_auto_recommend_prompt(st.session_state.clothing_profile)
            with st.spinner("正在生成轻量推荐策略，通常 30-90 秒内完成..."):
                st.session_state.auto_recommendation = call_text_model(
                    prompt,
                    temperature=0.25,
                    max_tokens=2200,
                    request_timeout=90,
                    thinking_type="disabled",
                )
            progress.success("推荐策略已生成")
        except Exception as exc:
            progress.error("自动推荐失败")
            st.error(f"自动推荐失败：{exc}")
            with st.expander("自动推荐诊断", expanded=True):
                st.json(st.session_state.get("last_api_event", {"status": "暂无请求记录"}))

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



def build_single_scene_prompt(clothing_profile: str, user_settings: str, video_index: int, used_scenes: str) -> str:
    return f"""
你是一名美区 TikTok 女装 UGC 场景规划师。

只规划 1 条视频的真实欧美生活场景，不写完整脚本，不生成图片，不生成视频。
这是第 {video_index} 条视频。请避免和已用场景重复。

【已用场景】
{used_scenes or "暂无"}

【款式资产卡】
{clothing_profile}

【用户设置】
{user_settings}

【输出要求】
只输出一个场景，格式如下：

### Scene Plan {video_index:02d}
scene family:
venue subtype:
micro location:
U.S. life context:
interior / layout:
physical props:
lighting:
ambient sound:
active task:
social context:
first motion cue:
clothing display logic:
compatible audience / selling point:
reject reason check:
""".strip()


def build_single_video_prompt(clothing_profile: str, user_settings: str, scene_plan: str, video_index: int, output_format: str = "Seedance 2.0 标准完整提示词") -> str:
    return f"""
你是一名美区 TikTok 女装带货 AI 视频提示词编导，专门写 Seedance 2.0 文本提示词。

请只生成 1 条视频提示词，这是 Video {video_index:02d}。
只输出文本，不生成图片，不生成视频。

【当前输出格式】
{output_format}

【输出格式执行规则】
- 如果是“Seedance 2.0 标准完整提示词”：输出完整的 Seedance 视频提示词，包含 Scene / First frame / Camera / Action timeline / Dialogue / Clothing display / Ending / Stability notes。
- 如果是“只要固定格式 Prompt”：只输出一段完整 Prompt，不展开解释，不输出多余标题。
- 如果是“分镜脚本”：按 0:00-0:03 / 0:03-0:08 / 0:08-0:12 / 0:12-0:15 输出分镜时间轴。

【硬性要求】
1. 15 秒，9:16，Seedance 2.0 全能参考模型。
2. 使用参考图人物和参考图服装，不要猜颜色。
3. 如果需要台词，英文台词后必须有中文翻译。
4. 只围绕服装本身展示版型、领口、腰线、裙摆、面料视觉、走动状态等。
5. 不要输出 Positive Prompt / Negative Prompt / Hashtags 旧格式。
6. TikTok UGC 真实感，不要摄影棚、大片、T台。
7. 严格遵守下面这个场景规划，不要换场景。

【款式资产卡】
{clothing_profile}

【用户设置】
{user_settings}

【场景规划】
{scene_plan}

【输出格式】
### Video {video_index:02d}
使用 Seedance 2.0 全能参考模型生成一条 15 秒竖屏 9:16 视频，原生 720P 分辨率，Standard 标准高清渲染模式，禁止 fast 低画质版本，开启高码率无损输出，视频码率 8Mbps 以上，保持参考图服装款式一致，保持人物主体自然真实，TikTok UGC 原生手持拍摄质感。

Scene:
First frame:
Camera:
Action timeline:
Dialogue / Voiceover:
Clothing display:
Ending / CTA:
Stability notes:
""".strip()



def render_generation(settings: Dict[str, Any]) -> None:
    st.subheader("4. 生成结果")
    st.markdown(
        "<div class='section-note'>本工具只输出 Seedance 2.0 文本提示词，不生成图片或视频。V31 改为逐条生成，可以看到每一条视频的当前进度，不再长时间停在一个总 spinner。</div>",
        unsafe_allow_html=True,
    )

    if st.button("生成 Seedance 2.0 文本提示词", type="primary", use_container_width=True, disabled=not bool(st.session_state.clothing_profile.strip())):
        try:
            user_settings = settings_to_text(settings)
            output_count_raw = settings.get("输出数量", 10)
            try:
                output_count = int(output_count_raw)
            except Exception:
                output_count = 10
            output_count = max(1, min(output_count, 30))

            st.session_state.scene_plan = ""
            st.session_state.generation_result = ""

            progress_bar = st.progress(0)
            status_line = st.empty()
            log_box = st.container()
            result_box = st.empty()

            scene_plans = []
            video_outputs = []
            logs = []

            for i in range(1, output_count + 1):
                used_scenes = "\n\n".join(scene_plans[-8:])

                status_line.info(f"任务进度：Video {i}/{output_count} · 正在规划场景骨架")
                logs.append(f"Video {i}/{output_count}：开始规划场景")
                with log_box:
                    st.write(logs[-1])

                scene_prompt = build_single_scene_prompt(
                    st.session_state.clothing_profile,
                    user_settings,
                    i,
                    used_scenes,
                )

                scene_plan = call_text_model(
                    scene_prompt,
                    temperature=0.85,
                    max_tokens=1600,
                    request_timeout=120,
                    thinking_type="disabled",
                )

                scene_plans.append(scene_plan)
                st.session_state.scene_plan = "\n\n".join(scene_plans)

                progress_bar.progress((i - 0.5) / output_count)
                status_line.info(f"任务进度：Video {i}/{output_count} · 场景完成，正在生成提示词")
                logs.append(f"Video {i}/{output_count}：场景完成，开始生成提示词")
                with log_box:
                    st.write(logs[-1])

                video_prompt = build_single_video_prompt(
                    st.session_state.clothing_profile,
                    user_settings,
                    scene_plan,
                    i,
                    settings.get("输出格式", "Seedance 2.0 标准完整提示词"),
                )

                video_output = call_text_model(
                    video_prompt,
                    temperature=0.85,
                    max_tokens=3600,
                    request_timeout=260,
                    thinking_type="enabled",
                )

                video_outputs.append(video_output)
                st.session_state.generation_result = "\n\n---\n\n".join(video_outputs)

                progress_bar.progress(i / output_count)
                status_line.success(f"任务进度：Video {i}/{output_count} 已完成")
                logs.append(f"Video {i}/{output_count}：已完成")
                with log_box:
                    st.write(logs[-1])

                result_box.markdown("#### 已生成内容预览")
                result_box.code(st.session_state.generation_result[-6000:] if st.session_state.generation_result else "", language="text")

            status_line.success("全部生成完成")
            st.success("生成完成")

        except Exception as exc:
            st.error(f"生成失败：{exc}")
            st.markdown(
                "<div class='warning-soft'>排查：1）确认 Streamlit Secrets 已保存并 Reboot；2）确认资产卡不为空；3）输出数量先用 3 或 5 测试；4）如果是 timeout，降低输出数量或稍后重试。</div>",
                unsafe_allow_html=True,
            )
            with st.expander("生成诊断", expanded=True):
                st.json(st.session_state.get("last_api_event", {"status": "暂无请求记录"}))

    if st.session_state.scene_plan:
        with st.expander("查看本批场景规划", expanded=False):
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
