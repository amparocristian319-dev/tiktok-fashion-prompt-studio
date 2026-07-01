"""Editable prompt templates for TikTok Fashion Prompt Studio.

You do NOT need to edit Python code for normal prompt changes.
Edit these Markdown files instead:

- prompt_templates/clothing_profile.md
- prompt_templates/auto_recommend.md
- prompt_templates/video_prompt_generator.md

Important:
- auto_recommend.md must keep {clothing_profile}
- video_prompt_generator.md must keep {clothing_profile} and {user_settings}
"""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR / "prompt_templates"


def _read_prompt(file_name: str) -> str:
    path = PROMPT_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"提示词文件不存在：{path}")
    return path.read_text(encoding="utf-8").strip()


CLOTHING_PROFILE_PROMPT = _read_prompt("clothing_profile.md")
AUTO_RECOMMEND_PROMPT = _read_prompt("auto_recommend.md")
VIDEO_PROMPT_GENERATOR_PROMPT = _read_prompt("video_prompt_generator.md")


def build_auto_recommend_prompt(clothing_profile: str) -> str:
    return AUTO_RECOMMEND_PROMPT.format(clothing_profile=clothing_profile)


def build_video_prompt(clothing_profile: str, user_settings: str) -> str:
    return VIDEO_PROMPT_GENERATOR_PROMPT.format(
        clothing_profile=clothing_profile,
        user_settings=user_settings,
    )
