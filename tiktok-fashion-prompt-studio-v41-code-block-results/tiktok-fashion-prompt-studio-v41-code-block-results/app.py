from __future__ import annotations

import csv
import io
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime
from PIL import Image
from typing import Any, Dict, List

import streamlit as st

# Self-contained config loader.
# Keep app.py independent from config.py, because Streamlit Cloud sometimes deploys app.py
# without sibling helper modules when the main file path or nested folder is misconfigured.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def _read_json_config(filename: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    path = DATA_DIR / filename
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[config-load-warning] {filename}: {exc}")
    return fallback


_FALLBACK_OPTIONS: Dict[str, Any] = {
    "VIDEO_GOALS": ["原生自然流", "TikTok Shop 转化", "测款素材", "服装卖点展示"],
    "OUTPUT_COUNTS": [3, 5, 10, 30],
    "OUTPUT_FORMATS": ["Seedance 2.0 标准完整提示词", "只要固定格式 Prompt", "分镜脚本"],
    "CONTENT_CATEGORIES": ["单人试穿展示", "GRWM 出门前穿搭", "路人夸赞/路人询问", "闺蜜/室友/男友反应", "TikTok Shop 软转化"],
    "SCRIPT_TYPES": {},
    "PERSONAS": ["自动判断"],
    "RELATIONSHIPS": ["自动判断"],
    "SCENES": ["自动判断"],
    "SHOT_STRUCTURES": ["自动判断"],
    "CAMERA_LANGUAGE": ["vertical 9:16", "stable phone UGC footage", "720P native output", "Standard HD render mode"],
    "EMOTIONAL_STYLES": ["realistic TikTok creator tone", "organic try-on moment"],
    "CONFLICTS": ["自动判断"],
    "PRODUCT_SELLING_POINTS": ["自动判断"],
    "VOICEOVER_STYLES": ["自动判断"],
    "CAPTION_STYLES": ["不要字幕"],
    "CTA_STYLES": ["弱 CTA", "自然 CTA", "评论区互动 CTA"],
    "DEDUP_LEVELS": ["高", "中", "低"],
    "STABILITY_MODES": ["平衡模式", "强稳定模式", "强创意模式"],
}

_FALLBACK_DEFAULTS: Dict[str, Any] = {
    "video_goals": [],
    "content_categories": [],
    "shot_structure": "自动判断",
    "output_count": 10,
    "output_format": "Seedance 2.0 标准完整提示词",
    "dedup_level": "高",
    "stability_mode": "平衡模式",
    "camera_language": ["vertical 9:16", "stable phone UGC footage", "720P native output", "Standard HD render mode"],
    "emotional_styles": ["realistic TikTok creator tone", "organic try-on moment"],
    "voiceover_style": ["自动判断"],
    "caption_style": ["不要字幕"],
    "cta_style": "弱 CTA",
}

OPTIONS = _read_json_config("options.json", _FALLBACK_OPTIONS)
DEFAULTS = _read_json_config("defaults.json", _FALLBACK_DEFAULTS)

VIDEO_GOALS = OPTIONS.get("VIDEO_GOALS", _FALLBACK_OPTIONS["VIDEO_GOALS"])
OUTPUT_COUNTS = OPTIONS.get("OUTPUT_COUNTS", _FALLBACK_OPTIONS["OUTPUT_COUNTS"])
OUTPUT_FORMATS = OPTIONS.get("OUTPUT_FORMATS", _FALLBACK_OPTIONS["OUTPUT_FORMATS"])
CONTENT_CATEGORIES = OPTIONS.get("CONTENT_CATEGORIES", _FALLBACK_OPTIONS["CONTENT_CATEGORIES"])
SCRIPT_TYPES = OPTIONS.get("SCRIPT_TYPES", {})
PERSONAS = OPTIONS.get("PERSONAS", _FALLBACK_OPTIONS["PERSONAS"])
RELATIONSHIPS = OPTIONS.get("RELATIONSHIPS", _FALLBACK_OPTIONS["RELATIONSHIPS"])
SCENES = OPTIONS.get("SCENES", _FALLBACK_OPTIONS["SCENES"])
SHOT_STRUCTURES = OPTIONS.get("SHOT_STRUCTURES", _FALLBACK_OPTIONS["SHOT_STRUCTURES"])
CAMERA_LANGUAGE = OPTIONS.get("CAMERA_LANGUAGE", _FALLBACK_OPTIONS["CAMERA_LANGUAGE"])
EMOTIONAL_STYLES = OPTIONS.get("EMOTIONAL_STYLES", _FALLBACK_OPTIONS["EMOTIONAL_STYLES"])
CONFLICTS = OPTIONS.get("CONFLICTS", _FALLBACK_OPTIONS["CONFLICTS"])
PRODUCT_SELLING_POINTS = OPTIONS.get("PRODUCT_SELLING_POINTS", _FALLBACK_OPTIONS["PRODUCT_SELLING_POINTS"])
VOICEOVER_STYLES = OPTIONS.get("VOICEOVER_STYLES", _FALLBACK_OPTIONS["VOICEOVER_STYLES"])
CAPTION_STYLES = OPTIONS.get("CAPTION_STYLES", _FALLBACK_OPTIONS["CAPTION_STYLES"])
CTA_STYLES = OPTIONS.get("CTA_STYLES", _FALLBACK_OPTIONS["CTA_STYLES"])
DEDUP_LEVELS = OPTIONS.get("DEDUP_LEVELS", _FALLBACK_OPTIONS["DEDUP_LEVELS"])
STABILITY_MODES = OPTIONS.get("STABILITY_MODES", _FALLBACK_OPTIONS["STABILITY_MODES"])

STATE_DIR = BASE_DIR / ".workspace_cache"
STATE_FILE = STATE_DIR / "workspace_state.json"
PERSIST_KEYS = [
    "clothing_profile",
    "clothing_profile_editor",
    "auto_recommendation",
    "generation_result",
    "scene_plan",
    "last_uploaded_name",
    "qiniu_image_hash",
    "qiniu_image_url",
    "qiniu_debug",
]


def load_workspace_state() -> Dict[str, Any]:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[workspace-load-warning] {exc}")
    return {}


def save_workspace_state() -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {key: st.session_state.get(key, "") for key in PERSIST_KEYS}
        data["_saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[workspace-save-warning] {exc}")


def clear_workspace_state() -> None:
    try:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
    except Exception as exc:
        print(f"[workspace-clear-warning] {exc}")
    for key in PERSIST_KEYS:
        if key in st.session_state:
            del st.session_state[key]


def workspace_state_info() -> Dict[str, Any]:
    data = load_workspace_state()
    return {
        "cache_file": str(STATE_FILE),
        "saved_at": data.get("_saved_at", "暂无"),
        "has_asset_card": bool((data.get("clothing_profile") or "").strip()),
        "has_generation_result": bool((data.get("generation_result") or "").strip()),
        "has_image_url": bool((data.get("qiniu_image_url") or "").strip()),
    }

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
    persisted = load_workspace_state()
    defaults = {
        "clothing_profile": "",
        "clothing_profile_editor": "",
        "auto_recommendation": "",
        "generation_result": "",
        "scene_plan": "",
        "last_uploaded_name": "",
        "qiniu_image_hash": "",
        "qiniu_image_url": "",
        "qiniu_debug": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = persisted.get(key, value)

    if not st.session_state.get("clothing_profile_editor") and st.session_state.get("clothing_profile"):
        st.session_state.clothing_profile_editor = st.session_state.clothing_profile


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
            value_text = ", ".join(map(str, value)) if value else "默认不填 / 让 AI 根据款式资产卡自动判断"
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


def split_video_blocks(markdown_text: str) -> List[str]:
    text = (markdown_text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?=###\s*Video\s*\d+|^Video\s*\d+|【视频编号】)", text, flags=re.IGNORECASE | re.MULTILINE)
    blocks = [p.strip().strip("-").strip() for p in parts if p.strip().strip("-").strip()]
    if not blocks:
        blocks = [text]
    return blocks


def video_block_label(block: str, index: int) -> str:
    first_line = block.splitlines()[0].strip() if block.splitlines() else ""
    m = re.search(r"(?:###\s*)?Video\s*(\d+)", first_line, flags=re.IGNORECASE)
    if m:
        return f"Video {int(m.group(1)):02d}"
    return f"Video {index:02d}"


def summarize_video_block(block: str) -> str:
    for marker in ["【总体分析】", "【分镜程式向逆推", "Scene:", "Action timeline:"]:
        if marker in block:
            after = block.split(marker, 1)[1].strip()
            first = re.sub(r"\s+", " ", after[:120]).strip()
            return first + ("..." if len(after) > 120 else "")
    plain = re.sub(r"\s+", " ", block[:120]).strip()
    return plain + ("..." if len(block) > 120 else "")


def render_result_viewer(result_text: str) -> None:
    blocks = split_video_blocks(result_text)
    st.markdown("### 结果查看区")
    st.markdown(
        f"<div class='section-note'>已生成 <b>{len(blocks)}</b> 条。按 Gemini 风格展示：一个提示词一个代码块，默认只展开第一条。</div>",
        unsafe_allow_html=True,
    )

    if not blocks:
        return

    for idx, block in enumerate(blocks):
        label = video_block_label(block, idx + 1)
        with st.expander(label, expanded=(idx == 0)):
            st.code(block, language="text")
            st.download_button(
                f"下载 {label} TXT",
                data=block.encode("utf-8"),
                file_name=f"{label.replace(' ', '_').lower()}_prompt.txt",
                mime="text/plain",
                use_container_width=True,
                key=f"download_code_block_{idx}",
            )


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
                    save_workspace_state()
                    st.success("参考图已上传，图片 URL 已就绪")
                except Exception as exc:
                    st.session_state.qiniu_image_hash = ""
                    st.session_state.qiniu_image_url = ""
                    st.session_state.qiniu_debug = {"error": str(exc)}
                    save_workspace_state()
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
                    save_workspace_state()
                    st.success("款式资产卡已生成")
                else:
                    st.session_state.clothing_profile = vision_brief
                    st.session_state.clothing_profile_editor = vision_brief
                    save_workspace_state()
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
        save_workspace_state()

    with st.expander("工作台缓存 / 刷新恢复", expanded=False):
        st.json(workspace_state_info())
        c1, c2 = st.columns(2)
        with c1:
            if st.button("保存当前工作台", use_container_width=True):
                save_workspace_state()
                st.success("已保存。刷新页面后会自动恢复资产卡、图片 URL、推荐策略和已生成结果。")
        with c2:
            if st.button("清空本地缓存", use_container_width=True):
                clear_workspace_state()
                st.success("已清空缓存，请刷新页面。")

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
                save_workspace_state()
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
        video_goals = st.multiselect(
            "视频目标（默认不填）",
            VIDEO_GOALS,
            default=safe_defaults(VIDEO_GOALS, DEFAULTS.get("video_goals", [])),
            placeholder="默认不填，让 AI 根据款式资产卡自动判断",
            help="不填就是默认模式。不要一开始勾很多目标，否则模型会把 TikTok Shop 转化、广告素材、Hook、评论区互动等方向全部混在一起。",
        )
        st.markdown("<div class='section-note'>视频目标默认留空即可。留空时系统会按资产卡自动判断，不会强行把拆快递、广告投放、评论区互动等方向混进每一条。</div>", unsafe_allow_html=True)
        try:
            default_output_count = int(DEFAULTS.get("output_count", 10))
        except Exception:
            default_output_count = 10
        output_count = st.number_input(
            "输出数量（自定义）",
            min_value=1,
            max_value=50,
            value=max(1, min(default_output_count, 50)),
            step=1,
            help="可以自定义数量。建议先用 3-5 条测试方向稳定后，再跑 10 条以上。",
        )
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
这是第 {video_index} 条视频。你的核心任务不是套固定场景，而是根据款式资产卡做真实场景适配，同时避免和本批已用场景重复。

【本批已用场景 / 已用开场任务】
{used_scenes or "暂无"}

【重复规避规则】
1. 这不是黑名单机制。不是永远禁止某个场景，而是同一批里已经出现过的 scene family / venue subtype / micro location / active task 不要再次使用。
2. 如果已用场景里出现过“洗衣房、自助洗衣、洗衣机、烘干机、laundromat、laundry room、washer、dryer、utility laundry area”，后续必须换成完全不同的生活空间。
3. 如果已用开场任务里出现过“拆快递、开箱、刚收到包裹、unboxing、package、delivery、try on after delivery”，后续必须换成新的开场任务，例如出门前检查穿搭、街头被夸、镜前调整、车内男友视角、餐厅/咖啡馆偶遇、商场走动、海滨/度假场景等。
4. TikTok Shop 转化只影响 CTA 或购买渠道，不等于每条都要写拆快递。除非用户明确选择“拆箱/开箱”，否则不要默认写收到快递、打开快递袋、刚拆包裹。
5. 场景必须优先匹配服装气质。不能为了“真实日常”而选择与服装气质明显不匹配的家务杂务场景。

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
repeat avoidance check:
""".strip()



def build_visual_truth_guard(clothing_profile: str) -> str:
    profile = (clothing_profile or "").lower()
    zh_profile = clothing_profile or ""

    rules = [
        "只允许写款式资产卡明确可见的服装结构；不确定、not clearly visible、看不清的内容一律不能写成卖点。",
        "不得为了增强带货效果而补充参考图未明确显示的口袋、拉链、纽扣、内衬、胸垫、开叉、腰带、鞋子、包包、首饰、价格、折扣、尺码效果、具体面料成分。",
    ]

    pocket_positive = ("口袋" in zh_profile or "pocket" in profile) and not (
        "不建议硬讲" in zh_profile and "口袋" in zh_profile
    )
    if not pocket_positive:
        rules.append("参考资产卡没有明确确认口袋可见：禁止出现 pocket / pockets / 口袋 / 插兜 / 隐形口袋 / 手插口袋 / it has pockets。")

    if not any(word in zh_profile for word in ["鞋", "凉鞋", "高跟鞋", "帆布鞋", "拖鞋"]) and not any(word in profile for word in ["shoe", "heels", "sandal", "sneaker"]):
        rules.append("参考资产卡没有明确确认鞋子可见：不要指定白色帆布鞋、细带高跟鞋、凉鞋等具体鞋款。")

    if not any(word in zh_profile for word in ["包", "托特", "手袋", "草编包"]) and not any(word in profile for word in ["bag", "tote", "purse"]):
        rules.append("参考资产卡没有明确确认包袋可见：不要指定草编包、托特包、小方包等配饰。")

    return "\n".join(f"- {rule}" for rule in rules)




def build_single_video_prompt(clothing_profile: str, user_settings: str, scene_plan: str, video_index: int, output_format: str = "Seedance 2.0 标准完整提示词") -> str:
    visual_truth_guard = build_visual_truth_guard(clothing_profile)
    return f"""
你是一名美区 TikTok 女装带货 AI 视频提示词编导，专门写 Seedance 2.0 全能参考模型可用的文本提示词。

请只生成 1 条视频提示词，这是 Video {video_index:02d}。
只输出文本，不生成图片，不生成视频。
你只按下面的通用输出格式生成。所有场景、道具、动作、台词、人物关系都必须基于资产卡与当前场景规划重新生成，不调用、不嵌入、不复用任何示例库内容。

【当前输出格式】
{output_format}

【输出格式总规则】
1. 默认使用“总体分析 + 分镜程式向逆推 + 时间轴动作台词一体化 + 服装稳定性控制”的通用结构。
2. 不再输出旧格式：Scene / First frame / Camera / Action timeline / Dialogue / Clothing display / Ending / CTA / Stability notes。
3. 格式可以参考这种字段层级，但内容必须全新生成；不得复用任何外部示例中的具体场景、道具、句式、人物设定或销售话术。
4. 如果是“只要固定格式 Prompt”，也必须保持这个结构，只是更短。
5. 如果是“分镜脚本”，重点强化时间轴，但仍要保留技术规格、场景设定、人物状态。

【硬性要求】
1. 15 秒，9:16，Seedance 2.0 全能参考模型。
2. 使用参考图人物和参考图服装，不要猜颜色；如果用户未填写颜色变体，写“人物主体如图所示 / 参考图服装”。
3. 英文台词后必须跟中文翻译。
4. 服装卖点必须绑定动作展示：领口、腰线、背面、裙摆、面料视觉、走动状态等。
5. 一条视频只保留 3-4 个主要动作，避免动作太满。
6. TikTok UGC 真实感，不要摄影棚、大片、T台。
7. 严格遵守下面这个场景规划，不要换场景。
8. 如果场景规划没有写“拆快递/开箱/刚收到包裹”，最终提示词不得自行添加拆快递、快递袋、开箱试穿、package delivery 逻辑。
9. TikTok Shop 只能作为自然购买渠道或弱 CTA，不能默认变成拆快递剧情。
10. 男友视角、闺蜜视角、路人视角都可以使用；不要把某个视角固定化，也不要因为参考材料中出现过就机械复用。

【视觉真实性硬约束】
{visual_truth_guard}

【款式资产卡】
{clothing_profile}

【用户设置】
{user_settings}

【场景规划】
{scene_plan}

【必须输出的格式】
### Video {video_index:02d}

【总体分析】
用 2-4 句话说明：视频类型、UGC 风格锚点、音景/对话关系、主要服装卖点。不要写成营销文案。

【分镜程式向逆推（15秒具体版本名）】
技术规格要求：使用 Seedance 2.0 全能参考模型（禁止使用 fast 版本），分辨率 720P，竖屏 9:16。
摄影风格：
【场景设定】：
【人物状态】：

【时间轴动作编排与台词（15秒）】：
0:00-0:03 ...
台词：...
0:03-0:07 ...
台词：...
0:07-0:11 ...
台词：...
0:11-0:15 ...
台词：...

【服装稳定性控制】
只写 4-6 条最高优先级控制，重点是保持参考图服装结构、避免错误添加、避免肢体/服装穿模、避免场景跑偏、避免字幕贴纸。
""".strip()




def generate_one_video_with_retry(
    video_prompt: str,
    primary_timeout: int = 600,
    fallback_timeout: int = 420,
) -> str:
    try:
        return call_text_model(
            video_prompt,
            temperature=0.85,
            max_tokens=4200,
            request_timeout=primary_timeout,
            thinking_type="enabled",
        )
    except Exception as first_exc:
        # Fallback keeps the same prompt but disables thinking and lowers token budget.
        # This prevents one slow item from stopping the whole batch.
        try:
            fallback_prompt = video_prompt + "\n\n【快速兜底要求】保持同一输出格式，但压缩表达，减少场景道具堆叠，确保完整返回一条可用提示词。"
            return call_text_model(
                fallback_prompt,
                temperature=0.78,
                max_tokens=3000,
                request_timeout=fallback_timeout,
                thinking_type="disabled",
            )
        except Exception as second_exc:
            raise RuntimeError(f"主生成失败：{first_exc}；兜底生成也失败：{second_exc}") from second_exc




def render_generation(settings: Dict[str, Any]) -> None:
    st.subheader("4. 生成结果")
    st.markdown(
        "<div class='section-note'>本工具只输出 Seedance 2.0 文本提示词，不生成图片或视频。逐条生成，完成一条就自动保存一条。结果按 Gemini 风格显示：一个提示词一个代码块。刷新后可恢复已完成内容；正在请求中的那一条若刷新，可能需要重跑。</div>",
        unsafe_allow_html=True,
    )

    if st.button("生成 Seedance 2.0 文本提示词", type="primary", use_container_width=True, disabled=not bool(st.session_state.clothing_profile.strip())):
        user_settings = settings_to_text(settings) + "\n\n【系统补充规则】TikTok Shop 转化只代表可以自然提及购买渠道或弱 CTA，不代表每条视频都要写成拆快递、开箱、刚收到包裹、package delivery。请优先使用多样化真实生活场景和开场任务。"
        output_count_raw = settings.get("输出数量", 10)
        try:
            target_count = int(output_count_raw)
        except Exception:
            target_count = 10
        target_count = max(1, min(target_count, 50))

        st.session_state.scene_plan = ""
        st.session_state.generation_result = ""

        progress_bar = st.progress(0)
        status_line = st.empty()
        log_box = st.container()
        result_box = st.empty()

        scene_plans: List[str] = []
        video_outputs: List[str] = []
        logs: List[str] = []
        failed_attempts: List[str] = []

        max_attempts = target_count * 2
        attempt = 0

        while len(video_outputs) < target_count and attempt < max_attempts:
            attempt += 1
            video_index = len(video_outputs) + 1
            used_scenes = "\n\n".join(scene_plans[-10:])

            try:
                status_line.info(f"任务进度：目标 {len(video_outputs)}/{target_count} · 正在规划 Video {video_index:02d} 场景")
                logs.append(f"Attempt {attempt}：开始规划 Video {video_index:02d}")
                with log_box:
                    st.write(logs[-1])

                scene_prompt = build_single_scene_prompt(
                    st.session_state.clothing_profile,
                    user_settings,
                    video_index,
                    used_scenes,
                )

                scene_plan = call_text_model(
                    scene_prompt,
                    temperature=0.9,
                    max_tokens=1900,
                    request_timeout=180,
                    thinking_type="disabled",
                )

                scene_plans.append(scene_plan)
                st.session_state.scene_plan = "\n\n".join(scene_plans)
                save_workspace_state()

                progress_bar.progress(min(0.95, len(video_outputs) / target_count))
                status_line.info(f"任务进度：Video {video_index:02d} 场景完成，正在生成提示词；如果深度生成超时，会自动走快速兜底")
                logs.append(f"Attempt {attempt}：Video {video_index:02d} 场景完成，开始生成提示词")
                with log_box:
                    st.write(logs[-1])

                video_prompt = build_single_video_prompt(
                    st.session_state.clothing_profile,
                    user_settings,
                    scene_plan,
                    video_index,
                    settings.get("输出格式", "Seedance 2.0 标准完整提示词"),
                )

                video_output = generate_one_video_with_retry(video_prompt)

                if not video_output or len(video_output.strip()) < 200:
                    raise RuntimeError("模型返回内容过短，已丢弃并重试下一次。")

                video_outputs.append(video_output)
                st.session_state.generation_result = "\n\n---\n\n".join(video_outputs)
                save_workspace_state()

                progress_bar.progress(len(video_outputs) / target_count)
                status_line.success(f"任务进度：已完成 {len(video_outputs)}/{target_count}")
                logs.append(f"Video {video_index:02d}：已完成")
                with log_box:
                    st.write(logs[-1])

                result_box.markdown(f"#### 最新完成：Video {video_index:02d}")
                result_box.code(video_output[-5000:] if video_output else "", language="text")

            except Exception as exc:
                failed_attempts.append(f"Attempt {attempt} / Video {video_index:02d} failed: {exc}")
                logs.append(f"Attempt {attempt} 失败，继续尝试下一条：{exc}")
                with log_box:
                    st.warning(logs[-1])
                save_workspace_state()
                continue

        if len(video_outputs) >= target_count:
            progress_bar.progress(1.0)
            status_line.success(f"全部生成完成：{len(video_outputs)}/{target_count}")
            st.success(f"生成完成：{len(video_outputs)} 条")
        else:
            status_line.warning(f"只完成 {len(video_outputs)}/{target_count}，已达到最大尝试次数 {max_attempts}。")
            st.warning("部分生成失败。可以降低输出数量，或稍后继续生成。已完成内容已保存。")

        if failed_attempts:
            with st.expander("失败尝试记录", expanded=False):
                for item in failed_attempts:
                    st.write(item)

    if st.session_state.scene_plan:
        with st.expander("查看本批场景规划", expanded=False):
            st.markdown(st.session_state.scene_plan)

    if st.session_state.generation_result:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_name = f"tiktok_fashion_prompts_{timestamp}.txt"
        csv_name = f"tiktok_fashion_prompts_{timestamp}.csv"

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("下载全部 TXT", data=st.session_state.generation_result.encode("utf-8"), file_name=txt_name, mime="text/plain", use_container_width=True)
        with col2:
            csv_text = rows_to_csv_text(parse_videos_to_rows(st.session_state.generation_result))
            st.download_button("下载全部 CSV", data=csv_text.encode("utf-8-sig"), file_name=csv_name, mime="text/csv", use_container_width=True)

        render_result_viewer(st.session_state.generation_result)

        with st.expander("查看全部原始结果", expanded=False):
            st.code(st.session_state.generation_result, language="text")


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
