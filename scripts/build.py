"""
ポータルセレクター用のデータを作る。

data/ にある掲載リスト（<名前>.json）ごとに、VRChat API から各ワールドのサムネを取ってアトラスにまとめ、
public/<名前>/worlds.json と public/<名前>/thumbs.jpg を書き出す。GitHub Actions から呼ばれるが、手元でもそのまま動く。

    python scripts/build.py
"""

import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "public"

FORMAT_VERSION = 1
THUMB_W, THUMB_H, COLS = 256, 144, 8
MAX_ATLAS = 2048
MAX_ITEMS = COLS * (MAX_ATLAS // THUMB_H)  # 8 × 14 = 112
MAX_JPEG_BYTES = 1_000_000
MAX_DESCRIPTION = 120  # 詳細画面の紹介文欄に収まる文字数

WORLD_ID = re.compile(r"^wrld_[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
API = "https://api.vrchat.cloud/api/1/worlds/"
USER_AGENT = "PhotoPortalBuilder/1.0 (VRChat world portal list; GitHub Actions)"
REQUEST_INTERVAL = 1.0  # VRChat API には1秒に1回まで
JST = timezone(timedelta(hours=9))


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read()


def fetch_world(world_id: str) -> dict | None:
    try:
        return json.loads(fetch(API + world_id))
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        warn(f"{world_id}: ワールド情報を取得できませんでした（{e}）")
        return None
    finally:
        time.sleep(REQUEST_INTERVAL)


def fetch_thumb(url: str, world_id: str) -> Image.Image | None:
    try:
        image = Image.open(io.BytesIO(fetch(url))).convert("RGB")
    except (urllib.error.URLError, OSError) as e:
        warn(f"{world_id}: サムネを取得できませんでした（{e}）")
        return None
    finally:
        time.sleep(REQUEST_INTERVAL)
    return fit_16_9(image)


def fit_16_9(image: Image.Image) -> Image.Image:
    """中央で 16:9 に切り抜いて 256×144 に縮小する"""
    w, h = image.size
    target = THUMB_W / THUMB_H
    if w / h > target:
        new_w = round(h * target)
        left = (w - new_w) // 2
        image = image.crop((left, 0, left + new_w, h))
    else:
        new_h = round(w / target)
        top = (h - new_h) // 2
        image = image.crop((0, top, w, top + new_h))
    return image.resize((THUMB_W, THUMB_H), Image.LANCZOS)


def shorten(text: str) -> str:
    """VRChat の説明文を詳細画面に収まる長さにする"""
    text = " ".join(text.split())
    return text if len(text) <= MAX_DESCRIPTION else text[: MAX_DESCRIPTION - 1] + "…"


def published_date(info: dict) -> str:
    """公開日（YYYY-MM-DD、日本時間）。一度も公開していなければ最初のアップロード日"""
    for key in ("publicationDate", "labsPublicationDate", "created_at"):
        value = info.get(key)
        if not value or value == "none":
            continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(JST).date().isoformat()
        except ValueError:
            continue
    return ""


def placeholder() -> Image.Image:
    return Image.new("RGB", (THUMB_W, THUMB_H), (38, 40, 50))


warnings: list[str] = []


def warn(message: str) -> None:
    warnings.append(message)
    print(f"::warning::{message}", file=sys.stderr)


def main() -> int:
    sources = sorted(DATA_DIR.glob("*.json"))
    for source in sources:
        build_source(source)
    print(f"\n{len(sources)} 個のリストを書き出しました（警告 {len(warnings)} 件）")
    return 0


def build_source(source: Path) -> None:
    name = source.stem
    print(f"== {name}")
    entries = json.loads(source.read_text(encoding="utf-8")).get("items", [])
    out_dir = OUT_DIR / name

    items = []
    thumbs = []
    seen = set()
    for entry in entries:
        world_id = str(entry.get("worldId", "")).strip()
        if not WORLD_ID.match(world_id):
            warn(f"worldId の形式が違うので飛ばしました: {world_id!r}")
            continue
        if world_id in seen:
            warn(f"{world_id}: 重複しているので2件目以降を飛ばしました")
            continue
        if len(items) >= MAX_ITEMS:
            warn(f"{MAX_ITEMS} 件を超えた分は載せられません: {world_id}")
            continue
        seen.add(world_id)

        info = fetch_world(world_id) or {}
        if info.get("releaseStatus") == "private" and not entry.get("allowPrivate"):
            warn(f"{world_id}: 非公開ワールドなので飛ばしました（ほかの人はポータルから入れません）")
            continue

        thumb_url = entry.get("thumbUrl") or info.get("thumbnailImageUrl") or info.get("imageUrl")
        thumb = fetch_thumb(thumb_url, world_id) if thumb_url else None
        if thumb is None:
            thumb = placeholder()

        items.append({
            "worldId": world_id,
            "title": entry.get("title") or info.get("name") or world_id,
            "author": entry.get("author") or info.get("authorName") or "",
            "description": entry.get("description") or shorten(info.get("description", "")),
            "publishedAt": entry.get("publishedAt") or published_date(info),
            "thumbIndex": len(thumbs),
        })
        thumbs.append(thumb)
        print(f"ok  {world_id}  {items[-1]['title']}")

    out_dir.mkdir(parents=True, exist_ok=True)
    write_atlas(thumbs, out_dir)
    data = {
        "version": FORMAT_VERSION,
        "updatedAt": datetime.now(JST).replace(microsecond=0).isoformat(),
        "thumb": {"width": THUMB_W, "height": THUMB_H, "cols": COLS},
        "items": items,
    }
    (out_dir / "worlds.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(items)} 件")


def write_atlas(thumbs: list[Image.Image], out_dir: Path) -> None:
    rows = max(1, (len(thumbs) + COLS - 1) // COLS)
    atlas = Image.new("RGB", (THUMB_W * COLS, THUMB_H * rows), (0, 0, 0))
    for i, thumb in enumerate(thumbs):
        atlas.paste(thumb, ((i % COLS) * THUMB_W, (i // COLS) * THUMB_H))

    # 1MB 以下に収まる一番高い品質で保存する
    for quality in range(90, 40, -5):
        buffer = io.BytesIO()
        atlas.save(buffer, "JPEG", quality=quality, optimize=True, progressive=False)
        if buffer.tell() <= MAX_JPEG_BYTES:
            break
    (out_dir / "thumbs.jpg").write_bytes(buffer.getvalue())
    print(f"thumbs.jpg  {atlas.width}×{atlas.height}  品質 {quality}  {buffer.tell() // 1024} KB")


if __name__ == "__main__":
    sys.exit(main())
