from __future__ import annotations

import csv
import io
import re
from datetime import datetime
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
from prompts import CLOTHING_PROFILE_PROMPT, build_auto_recommend_prompt, build_scene_plan_prompt, build_video_prompt
from volc_api import call_text_model, call_vision_model, get_secret

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
    st.markdown('<div class="sub-title">美区女装原生视频提示词生成器 · 场景深度规划 · CTA 自动判断 · 只生成文本</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-card">
          <div class="metric-grid">
            <div class="metric-card"><div class="metric-label">核心逻辑</div><div class="metric-value">图片分析 + 随机创意肉</div></div>
            <div class="metric-card"><div class="metric-label">场景逻辑</div><div class="metric-value">先规划 / 再生成</div></div>
            <div class="metric-card"><div class="metric-label">输出格式</div><div class="metric-value">15秒 9:16 Seedance Prompt</div></div>
            <div class="metric-card"><div class="metric-label">冲突控制</div><div class="metric-value">资产卡兼容过滤</div></div>
          </div>
        </div>
        """,
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
            f"<div class='section-note'>已上传：<b>{uploaded_file.name}</b> · {file_size_mb:.1f} MB。页面不展示大图，避免界面被图片撑开。</div>",
            unsafe_allow_html=True,
        )

        if st.button("分析款式资产", type="primary", use_container_width=True):
            with st.spinner("正在调用火山方舟模型分析服装款式... "):
                try:
                    mime_type = get_mime_type(uploaded_file.name)
                    st.session_state.clothing_profile = call_vision_model(
                        CLOTHING_PROFILE_PROMPT,
                        image_bytes=image_bytes,
                        mime_type=mime_type,
                    )
                    st.success("款式资产卡已生成")
                except Exception as exc:
                    st.error(f"分析失败：{exc}")

    st.subheader("2. 款式资产卡")
    st.markdown("<div class='section-note'>资产卡只分析款式、版型、结构、面料视觉、展示价值；默认不描述颜色。后续颜色在生成设置里单独填。</div>", unsafe_allow_html=True)
    clothing_profile_input = st.text_area(
        "可手动修正 AI 看错的地方",
        value=st.session_state.clothing_profile,
        height=420,
        key="clothing_profile_editor",
    )
    st.session_state.clothing_profile = clothing_profile_input

    if st.button("AI 自动推荐创意策略", use_container_width=True, disabled=not bool(st.session_state.clothing_profile.strip())):
        with st.spinner("正在根据款式资产卡推荐策略... "):
            try:
                prompt = build_auto_recommend_prompt(st.session_state.clothing_profile)
                st.session_state.auto_recommendation = call_text_model(prompt, temperature=0.5, max_tokens=5000)
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
    st.markdown("<div class='section-note'>本工具只生成 Seedance 2.0 文本提示词，不会生成图片或视频。</div>", unsafe_allow_html=True)
    if st.button("生成 Seedance 2.0 文本提示词", type="primary", use_container_width=True, disabled=not bool(st.session_state.clothing_profile.strip())):
        with st.spinner("第 1 步：正在进行本批场景深度规划... "):
            try:
                user_settings = settings_to_text(settings)
                if settings.get("每次生成前先进行场景深度规划", True):
                    scene_prompt = build_scene_plan_prompt(st.session_state.clothing_profile, user_settings)
                    st.session_state.scene_plan = call_text_model(scene_prompt, temperature=1.15, max_tokens=12000)
                else:
                    st.session_state.scene_plan = "未启用场景深度规划。"
            except Exception as exc:
                st.error(f"场景规划失败：{exc}")
                return

        with st.spinner("第 2 步：正在根据场景规划生成 Seedance 2.0 文本提示词... "):
            try:
                prompt = build_video_prompt(st.session_state.clothing_profile, user_settings, st.session_state.scene_plan)
                st.session_state.generation_result = call_text_model(prompt, temperature=0.85, max_tokens=30000)
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
    left, right = st.columns([0.38, 0.62], gap="large")
    with left:
        render_left_panel()
    with right:
        settings = render_settings_panel()
        render_generation(settings)


if __name__ == "__main__":
    main()
