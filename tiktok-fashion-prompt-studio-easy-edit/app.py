from __future__ import annotations

import csv
import io
import os
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
    PRODUCT_SELLING_POINTS,
    RELATIONSHIPS,
    SCENES,
    SCRIPT_TYPES,
    SHOT_STRUCTURES,
    STABILITY_MODES,
    VIDEO_GOALS,
    VOICEOVER_STYLES,
)
from prompts import CLOTHING_PROFILE_PROMPT, build_auto_recommend_prompt, build_video_prompt
from volc_api import call_text_model, call_vision_model, get_secret

load_dotenv()

st.set_page_config(
    page_title="TikTok Fashion Prompt Studio",
    page_icon="👗",
    layout="wide",
)


def check_password() -> bool:
    """Simple password gate for online deployment.

    Set APP_PASSWORD in .env or in the hosting platform secrets.
    If APP_PASSWORD is empty, the app will run in open mode and show a warning.
    """
    app_password = get_secret("APP_PASSWORD")

    if not app_password:
        st.warning("当前没有设置 APP_PASSWORD。部署到公网前，请务必在环境变量里设置登录密码。")
        return True

    if st.session_state.get("authenticated") is True:
        return True

    st.title("TikTok Fashion Prompt Studio")
    st.caption("请输入访问密码后使用。")

    with st.form("login_form"):
        password = st.text_input("访问密码", type="password")
        submitted = st.form_submit_button("进入")

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


def flatten_script_types() -> List[str]:
    result: List[str] = []
    for group, items in SCRIPT_TYPES.items():
        result.extend([f"{group} / {item}" for item in items])
    return result


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
    """Return a safe index even after editing data/defaults.json."""
    try:
        return options.index(value)
    except ValueError:
        return fallback


def safe_defaults(options: List[Any], defaults: List[Any]) -> List[Any]:
    """Keep only default values that still exist in the option list."""
    return [item for item in defaults if item in options]


def parse_videos_to_rows(markdown_text: str) -> List[Dict[str, str]]:
    """Best-effort parser for CSV export.

    The model output is Markdown-like. This parser splits by 【视频编号】 and stores
    each block as one row. You can improve this later if you force JSON output.
    """
    blocks = re.split(r"(?=【视频编号】)", markdown_text)
    rows: List[Dict[str, str]] = []
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
        title_match = re.search(r"【视频方向】\s*\n?(.+)", block)
        structure_match = re.search(r"【拍摄结构】\s*\n?(.+)", block)
        hook_match = re.search(r"【3秒 Hook】\s*\n?(.+)", block)
        rows.append(
            {
                "index": str(len(rows) + 1),
                "video_direction": title_match.group(1).strip() if title_match else "",
                "shot_structure": structure_match.group(1).strip() if structure_match else "",
                "hook": hook_match.group(1).strip() if hook_match else "",
                "full_text": block,
            }
        )
    if not rows and markdown_text.strip():
        rows.append({"index": "1", "video_direction": "", "shot_structure": "", "hook": "", "full_text": markdown_text.strip()})
    return rows


def rows_to_csv_text(rows: List[Dict[str, str]]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["index", "video_direction", "shot_structure", "hook", "full_text"])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render_header() -> None:
    st.title("TikTok Fashion Prompt Studio")
    st.caption("美区女装原生短视频提示词生成器 · 服装图片分析 · 创意控制台 · Seedance2.0 Prompt")
    with st.expander("后续怎么修改这个工具？", expanded=False):
        st.markdown(
            """
            - 改下拉选项、脚本类型、人设、场景：编辑 `data/options.json`。
            - 改默认勾选项：编辑 `data/defaults.json`。
            - 改服装分析提示词：编辑 `prompt_templates/clothing_profile.md`。
            - 改自动推荐逻辑：编辑 `prompt_templates/auto_recommend.md`。
            - 改最终 Seedance 提示词生成逻辑：编辑 `prompt_templates/video_prompt_generator.md`。
            - 改完后在 GitHub 点 `Commit changes`，Streamlit Cloud 会自动更新。
            """
        )


def render_left_panel() -> None:
    st.subheader("1. 上传服装图片")
    uploaded_file = st.file_uploader("上传 jpg / jpeg / png / webp", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file is not None:
        st.session_state.last_uploaded_name = uploaded_file.name
        image_bytes = uploaded_file.getvalue()
        st.image(image_bytes, caption=uploaded_file.name, use_container_width=True)

        if st.button("分析衣服", type="primary", use_container_width=True):
            with st.spinner("正在调用火山方舟模型分析服装图片..."):
                try:
                    mime_type = get_mime_type(uploaded_file.name)
                    st.session_state.clothing_profile = call_vision_model(
                        CLOTHING_PROFILE_PROMPT,
                        image_bytes=image_bytes,
                        mime_type=mime_type,
                    )
                    st.success("服装资产卡已生成")
                except Exception as exc:
                    st.error(f"分析失败：{exc}")

    st.subheader("2. 服装资产卡")
    clothing_profile_input = st.text_area(
        "你可以直接编辑资产卡，修正 AI 看错的地方。",
        value=st.session_state.clothing_profile,
        height=480,
        key="clothing_profile_editor",
    )
    st.session_state.clothing_profile = clothing_profile_input

    if st.button("AI 自动推荐设置", use_container_width=True, disabled=not bool(st.session_state.clothing_profile.strip())):
        with st.spinner("正在根据服装资产卡推荐设置..."):
            try:
                prompt = build_auto_recommend_prompt(st.session_state.clothing_profile)
                st.session_state.auto_recommendation = call_text_model(prompt, temperature=0.5, max_tokens=5000)
                st.success("推荐设置已生成")
            except Exception as exc:
                st.error(f"自动推荐失败：{exc}")

    if st.session_state.auto_recommendation:
        with st.expander("查看 AI 自动推荐设置", expanded=True):
            st.markdown(st.session_state.auto_recommendation)


def render_settings_panel() -> Dict[str, Any]:
    st.subheader("3. 视频生成控制台")

    with st.expander("基础设置", expanded=True):
        video_goals = st.multiselect("视频目标", VIDEO_GOALS, default=safe_defaults(VIDEO_GOALS, DEFAULTS.get("video_goals", [])))
        output_count = st.selectbox(
            "输出数量",
            OUTPUT_COUNTS,
            index=safe_index(OUTPUT_COUNTS, DEFAULTS.get("output_count", OUTPUT_COUNTS[0])),
            help="100 条会消耗更多 token。第一次建议先测 10 或 30 条。",
        )
        output_format = st.selectbox(
            "输出格式",
            OUTPUT_FORMATS,
            index=safe_index(OUTPUT_FORMATS, DEFAULTS.get("output_format", OUTPUT_FORMATS[0])),
        )

    with st.expander("创意方向", expanded=True):
        content_categories = st.multiselect(
            "内容大类",
            CONTENT_CATEGORIES,
            default=safe_defaults(CONTENT_CATEGORIES, DEFAULTS.get("content_categories", [])),
        )
        selected_script_types = st.multiselect(
            "细分脚本类型",
            flatten_script_types(),
            default=[],
            help="不选则由 AI 根据服装资产卡和内容大类自动选择。",
        )
        conflicts = st.multiselect("剧情冲突", CONFLICTS, default=[])
        selling_points = st.multiselect("服装卖点重点", PRODUCT_SELLING_POINTS, default=[])

    with st.expander("人物与场景", expanded=False):
        personas = st.multiselect("人物人设", PERSONAS, default=[])
        relationships = st.multiselect("人物关系", RELATIONSHIPS, default=["单人自拍"])
        scenes = st.multiselect("拍摄场景", SCENES, default=[])

    with st.expander("拍摄控制", expanded=False):
        shot_structure = st.selectbox(
            "拍摄结构",
            SHOT_STRUCTURES,
            index=safe_index(SHOT_STRUCTURES, DEFAULTS.get("shot_structure", SHOT_STRUCTURES[0])),
        )
        camera_language = st.multiselect(
            "镜头语言",
            CAMERA_LANGUAGE,
            default=["handheld phone camera", "vertical 9:16", "natural daylight"],
        )
        stability_mode = st.selectbox(
            "AI 稳定性",
            STABILITY_MODES,
            index=safe_index(STABILITY_MODES, DEFAULTS.get("stability_mode", STABILITY_MODES[0])),
        )
        if any(item in relationships for item in ["闺蜜", "室友", "男朋友", "妈妈", "陌生女生", "商场路人", "gay bestie stylist", "街拍采访者"]):
            st.warning("多人视频 AI 稳定性较低。建议 2 人以内，镜头不要太复杂。")

    with st.expander("语言与转化", expanded=False):
        emotional_styles = st.multiselect("情绪风格", EMOTIONAL_STYLES, default=["realistic TikTok creator tone", "not gatekeeping"])
        voiceover_style = st.multiselect("口播风格", VOICEOVER_STYLES, default=["自言自语式"])
        caption_style = st.multiselect("字幕风格", CAPTION_STYLES, default=["lowercase TikTok captions"])
        cta_style = st.selectbox("CTA 风格", CTA_STYLES, index=safe_index(CTA_STYLES, "弱 CTA"))

    with st.expander("高级设置", expanded=False):
        dedup_level = st.selectbox("创意去重强度", DEDUP_LEVELS, index=safe_index(DEDUP_LEVELS, DEFAULTS.get("dedup_level", DEDUP_LEVELS[-1])), help="建议选高，一件衣服生成多条视频更不容易重复。")
        allow_auto_recommend = st.checkbox("允许 AI 自动推荐未选择项", value=True)
        exclude_low_stability = st.checkbox("排除低稳定脚本", value=True)
        prioritize_clothing_details = st.checkbox("优先突出服装细节", value=True)
        avoid_hard_ads = st.checkbox("避免硬广语气", value=True)
        use_us_tiktok_slang = st.checkbox("生成美国 TikTok 口语", value=True)

    return {
        "视频目标": video_goals,
        "输出数量": output_count,
        "输出格式": output_format,
        "内容大类": content_categories,
        "细分脚本类型": selected_script_types,
        "剧情冲突": conflicts,
        "服装卖点重点": selling_points,
        "人物人设": personas,
        "人物关系": relationships,
        "拍摄场景": scenes,
        "拍摄结构": shot_structure,
        "镜头语言": camera_language,
        "AI 稳定性": stability_mode,
        "情绪风格": emotional_styles,
        "口播风格": voiceover_style,
        "字幕风格": caption_style,
        "CTA 风格": cta_style,
        "创意去重强度": dedup_level,
        "允许 AI 自动推荐未选择项": allow_auto_recommend,
        "排除低稳定脚本": exclude_low_stability,
        "优先突出服装细节": prioritize_clothing_details,
        "避免硬广语气": avoid_hard_ads,
        "生成美国 TikTok 口语": use_us_tiktok_slang,
    }


def render_generation(settings: Dict[str, Any]) -> None:
    st.subheader("4. 生成结果")

    if st.button("生成视频提示词", type="primary", use_container_width=True, disabled=not bool(st.session_state.clothing_profile.strip())):
        with st.spinner("正在生成 TikTok 女装视频提示词..."):
            try:
                user_settings = settings_to_text(settings)
                prompt = build_video_prompt(st.session_state.clothing_profile, user_settings)
                st.session_state.generation_result = call_text_model(
                    prompt,
                    temperature=0.85,
                    max_tokens=30000,
                )
                st.success("生成完成")
            except Exception as exc:
                st.error(f"生成失败：{exc}")

    if st.session_state.generation_result:
        st.markdown(st.session_state.generation_result)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_name = f"tiktok_fashion_prompts_{timestamp}.txt"
        csv_name = f"tiktok_fashion_prompts_{timestamp}.csv"

        st.text_area(
            "复制全部结果：点击文本框后 Ctrl+A / Ctrl+C",
            st.session_state.generation_result,
            height=260,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "下载 TXT",
                data=st.session_state.generation_result.encode("utf-8"),
                file_name=txt_name,
                mime="text/plain",
                use_container_width=True,
            )
        with col2:
            csv_text = rows_to_csv_text(parse_videos_to_rows(st.session_state.generation_result))
            st.download_button(
                "下载 CSV",
                data=csv_text.encode("utf-8-sig"),
                file_name=csv_name,
                mime="text/csv",
                use_container_width=True,
            )


def main() -> None:
    if not check_password():
        return

    init_state()
    render_header()

    left, right = st.columns([0.42, 0.58], gap="large")
    with left:
        render_left_panel()
    with right:
        settings = render_settings_panel()
        render_generation(settings)


if __name__ == "__main__":
    main()
