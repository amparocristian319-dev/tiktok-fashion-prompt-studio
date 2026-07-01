"""Editable configuration for TikTok Fashion Prompt Studio.

You do NOT need to edit Python code for normal changes.
Edit these two files instead:

- data/options.json   -> dropdown / multiselect options
- data/defaults.json  -> default selected values

The variables below are loaded from JSON so app.py can keep using normal names.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OPTIONS_PATH = DATA_DIR / "options.json"
DEFAULTS_PATH = DATA_DIR / "defaults.json"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在：{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"配置文件 JSON 格式错误：{path}\n{exc}") from exc


OPTIONS = _read_json(OPTIONS_PATH)
DEFAULTS = _read_json(DEFAULTS_PATH)

VIDEO_GOALS = OPTIONS["VIDEO_GOALS"]
OUTPUT_COUNTS = OPTIONS["OUTPUT_COUNTS"]
OUTPUT_FORMATS = OPTIONS["OUTPUT_FORMATS"]
CONTENT_CATEGORIES = OPTIONS["CONTENT_CATEGORIES"]
SCRIPT_TYPES = OPTIONS["SCRIPT_TYPES"]
PERSONAS = OPTIONS["PERSONAS"]
RELATIONSHIPS = OPTIONS["RELATIONSHIPS"]
SCENES = OPTIONS["SCENES"]
SHOT_STRUCTURES = OPTIONS["SHOT_STRUCTURES"]
CAMERA_LANGUAGE = OPTIONS["CAMERA_LANGUAGE"]
EMOTIONAL_STYLES = OPTIONS["EMOTIONAL_STYLES"]
CONFLICTS = OPTIONS["CONFLICTS"]
PRODUCT_SELLING_POINTS = OPTIONS["PRODUCT_SELLING_POINTS"]
VOICEOVER_STYLES = OPTIONS["VOICEOVER_STYLES"]
CAPTION_STYLES = OPTIONS["CAPTION_STYLES"]
CTA_STYLES = OPTIONS["CTA_STYLES"]
DEDUP_LEVELS = OPTIONS["DEDUP_LEVELS"]
STABILITY_MODES = OPTIONS["STABILITY_MODES"]
