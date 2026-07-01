"""Qiniu Kodo image hosting helper.

Uploads the compressed image to Qiniu Kodo and returns a public image URL.
This avoids sending large base64 image payloads to the model API.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import quote

from qiniu import Auth, put_data

from volc_api import get_secret


def has_image_hosting_config() -> bool:
    return bool(
        get_secret("QINIU_ACCESS_KEY")
        and get_secret("QINIU_SECRET_KEY")
        and get_secret("QINIU_BUCKET")
        and get_secret("QINIU_DOMAIN")
    )


def get_image_hosting_status() -> Dict[str, str]:
    return {
        "provider": "qiniu",
        "image_hosting": "已配置" if has_image_hosting_config() else "未配置",
        "bucket": get_secret("QINIU_BUCKET", "未配置"),
        "domain": get_secret("QINIU_DOMAIN", "未配置"),
        "scheme": get_secret("QINIU_SCHEME", "http"),
        "prefix": get_secret("QINIU_PREFIX", "fashion-uploads"),
    }


def _clean_domain(domain: str) -> str:
    domain = domain.strip()
    domain = domain.replace("https://", "").replace("http://", "")
    return domain.strip("/")


def _build_public_url(domain: str, key: str, scheme: str) -> str:
    domain = _clean_domain(domain)
    scheme = (scheme or "http").replace("://", "").strip()
    # keep folder slashes but quote Chinese / special file characters
    safe_key = quote(key, safe="/")
    return f"{scheme}://{domain}/{safe_key}"


def upload_to_qiniu(
    image_bytes: bytes,
    original_filename: str = "fashion-reference.jpg",
    mime_type: str = "image/jpeg",
) -> Tuple[str, Dict[str, Any]]:
    access_key = get_secret("QINIU_ACCESS_KEY")
    secret_key = get_secret("QINIU_SECRET_KEY")
    bucket = get_secret("QINIU_BUCKET")
    domain = get_secret("QINIU_DOMAIN")
    scheme = get_secret("QINIU_SCHEME", "http")
    prefix = get_secret("QINIU_PREFIX", "fashion-uploads").strip().strip("/")

    if not all([access_key, secret_key, bucket, domain]):
        raise RuntimeError("七牛云上传未配置完整。请填写 QINIU_ACCESS_KEY / QINIU_SECRET_KEY / QINIU_BUCKET / QINIU_DOMAIN。")

    suffix = Path(original_filename or "fashion-reference.jpg").suffix.lower()
    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        suffix = ".jpg"

    digest = hashlib.sha1(image_bytes).hexdigest()[:16]
    day = datetime.now().strftime("%Y%m%d")
    key = f"{prefix}/{day}/{int(time.time())}_{digest}{suffix}"

    auth = Auth(access_key, secret_key)
    token = auth.upload_token(bucket, key, 3600)

    ret, info = put_data(
        token,
        key,
        image_bytes,
        mime_type=mime_type,
        check_crc=True,
    )

    status_code = getattr(info, "status_code", None)
    if status_code != 200:
        raise RuntimeError(f"七牛云上传失败，status={status_code}，info={info}")

    public_url = _build_public_url(domain, key, scheme)

    debug = {
        "provider": "qiniu",
        "bucket": bucket,
        "domain": _clean_domain(domain),
        "scheme": scheme,
        "key": key,
        "public_url": public_url,
        "bytes": len(image_bytes),
        "mime_type": mime_type,
        "response": ret or {},
    }
    return public_url, debug
