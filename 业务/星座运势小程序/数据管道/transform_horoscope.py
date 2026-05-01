"""标准化星座运势数据为小程序格式

读取现有 fetcher 输出的 JSON，补充元数据（星座属性、评分、标签等），
输出小程序云函数可直接消费的格式。
"""

import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

BEIJING_TZ = timezone(timedelta(hours=8))

FETCHER_OUTPUT_DIR = Path("/Users/mac/Documents/我的知识库/生活/星座运势")
FETCHER_LATEST = FETCHER_OUTPUT_DIR / "latest.json"

MP_OUTPUT_DIR = Path("/Users/mac/Documents/我的知识库/业务/星座运势小程序/数据管道/output")
MP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SIGN_META: dict[str, dict[str, str]] = {
    "aries":       {"date_range": "3.21 - 4.19", "element": "火象", "planet": "火星"},
    "taurus":      {"date_range": "4.20 - 5.20", "element": "土象", "planet": "金星"},
    "gemini":      {"date_range": "5.21 - 6.21", "element": "风象", "planet": "水星"},
    "cancer":      {"date_range": "6.22 - 7.22", "element": "水象", "planet": "月​亮"},
    "leo":         {"date_range": "7.23 - 8.22", "element": "火象", "planet": "太阳"},
    "virgo":       {"date_range": "8.23 - 9.22", "element": "土象", "planet": "水星"},
    "libra":       {"date_range": "9.23 - 10.23", "element": "风象", "planet": "金星"},
    "scorpio":     {"date_range": "10.24 - 11.22", "element": "水象", "planet": "冥王星"},
    "sagittarius": {"date_range": "11.23 - 12.21", "element": "火象", "planet": "木星"},
    "capricorn":   {"date_range": "12.22 - 1.19", "element": "土象", "planet": "土星"},
    "aquarius":    {"date_range": "1.20 - 2.18", "element": "风象", "planet": "天王星"},
    "pisces":      {"date_range": "2.19 - 3.20", "element": "水象", "planet": "海王星"},
}

LUCKY_COLORS = ["金色", "红色", "蓝色", "绿色", "紫色", "橙色", "银色", "粉色", "白色", "黄色", "棕色", "灰色"]


@dataclass
class SignFortune:
    sign_key: str
    sign_zh: str
    sign_en: str
    date_range: str
    element: str
    planet: str
    lucky_number: int
    lucky_color: str
    rating: int  # 1-5
    content: str
    tags: list[str]


def load_fetcher_output(path: Path | None = None) -> dict[str, Any]:
    """加载 fetcher 的 latest.json"""
    filepath = path or FETCHER_LATEST
    if not filepath.exists():
        raise FileNotFoundError(f"Fetcher output not found: {filepath}")
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def extract_sign_data(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """从 fetcher 原始输出中提取每个星座的数据，TianAPI（中文）优先"""
    merged: dict[str, dict[str, Any]] = {}
    sources = raw.get("sources", {})

    # TianAPI 优先（中文内容），其余按顺序兜底
    ordered_sources = sorted(
        sources.items(),
        key=lambda x: 0 if x[0] == "tianapi" else 1,
    )

    for source_key, source_data in ordered_sources:
        if not source_data.get("fetch_ok"):
            continue
        for sign_key, sign_data in source_data.get("signs", {}).items():
            if sign_key not in merged:
                merged[sign_key] = {
                    "sign_key": sign_data.get("sign_key", sign_key),
                    "sign_zh": sign_data.get("sign_zh", ""),
                    "sign_en": sign_data.get("sign_en", ""),
                    "content": "",
                    "lucky_number": None,
                    "sources": [],
                }
            merged[sign_key]["content"] = sign_data.get("content", merged[sign_key]["content"])
            if sign_data.get("lucky_number") and not merged[sign_key]["lucky_number"]:
                merged[sign_key]["lucky_number"] = sign_data["lucky_number"]
            merged[sign_key]["sources"].append(source_key)
    return merged


def assign_tags(content: str) -> list[str]:
    """根据内容关键词分配标签"""
    tags: list[str] = []
    if any(w in content for w in ["爱", "Love", "love", "感情", "桃花", "伴侣"]):
        tags.append("爱情")
    if any(w in content for w in ["财", "Money", "money", "收入", "投资", "理财"]):
        tags.append("财运")
    if any(w in content for w in ["工作", "Work", "work", "职业", "事业", "Career", "career"]):
        tags.append("事业")
    if any(w in content for w in ["健康", "Health", "health", "身体", "活力"]):
        tags.append("健康")
    if not tags:
        tags.append("综合")
    return tags


def clean_content(text: str) -> str:
    """清理 HTML 标签，提取纯文本"""
    import re
    # remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # remove leading source attribution if present
    text = re.sub(r"^AstroSage\.com[,.\s]*", "", text)
    text = re.sub(r"^Clickastro\.com[,.\s]*", "", text)
    return text.strip()


def compute_rating(content: str, lucky_number: int | None) -> int:
    """基于内容情绪和幸运数字计算 1-5 评分"""
    positive_words = [
        "good", "great", "excellent", "wonderful", "positive", "fortunate",
        "lucky", "best", "success", "progress", "opportunity", "幸运",
        "顺利", "好运", "进步", "成功", "机会"
    ]
    negative_words = [
        "bad", "terrible", "unfortunate", "caution", "difficult",
        "challenge", "avoid", "problem", "困难", "挑战", "谨慎",
        "避免", "不好", "小心"
    ]
    content_lower = content.lower()

    score = 3  # neutral baseline
    for w in positive_words:
        if w in content_lower:
            score += 0.2
    for w in negative_words:
        if w in content_lower:
            score -= 0.3

    # lucky number bonus
    if lucky_number and lucky_number >= 7:
        score += 0.3

    return max(1, min(5, round(score)))


def transform(raw: dict[str, Any] | None = None, input_path: Path | None = None) -> dict[str, Any]:
    """主转换函数

    Args:
        raw: 已加载的 fetcher 输出 dict
        input_path: 或指定 JSON 文件路径

    Returns:
        小程序格式的标准化数据
    """
    if raw is None:
        raw = load_fetcher_output(input_path)

    date_str = raw.get("date", datetime.now(BEIJING_TZ).strftime("%Y-%m-%d"))
    sign_data = extract_sign_data(raw)

    # 为随机颜色设置当天种子，保证同一天输出一致
    rng = random.Random(date_str)

    fortunes: dict[str, dict[str, Any]] = {}
    for sign_key in SIGN_META:
        meta = SIGN_META[sign_key]
        sign = sign_data.get(sign_key, {})
        content = clean_content(sign.get("content", ""))
        lucky_number = sign.get("lucky_number") or rng.randint(1, 9)

        rating = compute_rating(content, lucky_number)
        tags = assign_tags(content)

        fortunes[sign_key] = {
            "sign_key": sign_key,
            "sign_zh": sign.get("sign_zh", meta.get("sign_zh", "")),
            "sign_en": sign.get("sign_en", meta.get("sign_en", "")),
            "date_range": meta["date_range"],
            "element": meta["element"],
            "planet": meta["planet"],
            "lucky_number": lucky_number,
            "lucky_color": rng.choice(LUCKY_COLORS),
            "rating": rating,
            "content": content,
            "tags": tags,
        }

    return {
        "date": date_str,
        "generated_at": datetime.now(BEIJING_TZ).isoformat(),
        "signs": fortunes,
    }


def save_output(data: dict[str, Any], date_str: str | None = None) -> Path:
    """保存转换后的 JSON"""
    date_str = date_str or data["date"]
    filepath = MP_OUTPUT_DIR / f"mp_fortunes_{date_str}.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    latest_path = MP_OUTPUT_DIR / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="转换星座运势数据为小程序格式")
    parser.add_argument("--input", type=Path, help="Fetcher JSON 文件路径，默认读取 latest.json")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 JSON 到 stdout，不写入文件")
    args = parser.parse_args()

    raw = load_fetcher_output(args.input)
    data = transform(raw)

    if args.dry_run:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    filepath = save_output(data, data["date"])
    print(f"✅ 已转换: {filepath}")
    print(f"   星座数: {len(data['signs'])}")
    print(f"   日期: {data['date']}")


if __name__ == "__main__":
    main()
