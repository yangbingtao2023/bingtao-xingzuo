"""每日星座运势抓取脚本

从 TianAPI（中文）+ AstroSage / ClickAstro RSS（英文兜底）抓取当日运势。
"""

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import feedparser
import requests

# --- 配置 ---

RSS_FEEDS: dict[str, str] = {
    "astrosage": "https://feeds.feedburner.com/dayhoroscope",
    "clickastro": "http://feeds.feedburner.com/clickastro/daily-horoscope",
}

TIANAPI_KEY = os.environ.get("TIANAPI_KEY", "")
TIANAPI_BASE = "https://apis.tianapi.com/star/index"

KB_ROOT = Path(os.environ.get("KB_ROOT", "/Users/mac/Documents/我的知识库"))
OUTPUT_DIR = KB_ROOT / "生活/星座运势"

# 星座名称映射（英文 → 中文 + 简称）
SIGN_MAP: dict[str, dict[str, str]] = {
    "aries":       {"zh": "白羊座", "en": "Aries"},
    "taurus":      {"zh": "金牛座", "en": "Taurus"},
    "gemini":      {"zh": "双子座", "en": "Gemini"},
    "cancer":      {"zh": "巨蟹座", "en": "Cancer"},
    "leo":         {"zh": "狮子座", "en": "Leo"},
    "virgo":       {"zh": "处女座", "en": "Virgo"},
    "libra":       {"zh": "天秤座", "en": "Libra"},
    "scorpio":     {"zh": "天蝎座", "en": "Scorpio"},
    "sagittarius": {"zh": "射手座", "en": "Sagittarius"},
    "capricorn":   {"zh": "摩羯座", "en": "Capricorn"},
    "aquarius":    {"zh": "水瓶座", "en": "Aquarius"},
    "pisces":      {"zh": "双鱼座", "en": "Pisces"},
}

# --- 数据模型 ---

@dataclass
class SignHoroscope:
    sign_key: str
    sign_zh: str
    sign_en: str
    title: str
    content: str
    lucky_number: int | None = None
    pub_date: str | None = None


@dataclass
class SourceData:
    source: str
    name: str
    feed_url: str
    fetch_ok: bool
    error: str | None = None
    signs: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class DailyReport:
    date: str
    fetched_at: str
    sources: dict[str, dict[str, Any]] = field(default_factory=dict)


# --- 解析逻辑 ---

LUCKY_RE = re.compile(r"Lucky\s*Number[:\s]*(?:</?\w+>)?\s*(\d+)", re.IGNORECASE)

BEIJING_TZ = timezone(timedelta(hours=8))


def extract_lucky_number(text: str) -> int | None:
    m = LUCKY_RE.search(text)
    return int(m.group(1)) if m else None


def parse_astrosage(feed: Any) -> dict[str, SignHoroscope]:
    """解析 AstroSage RSS，格式：Aries Horoscope 1 May 2026"""
    results: dict[str, SignHoroscope] = {}
    for entry in feed.entries:
        title = entry.title or ""
        # 从 title 提取星座：如 "Aries Horoscope  1 May 2026"
        sign_match = re.match(r"(\w+)\s+Horoscope", title, re.IGNORECASE)
        if not sign_match:
            continue
        sign_en = sign_match.group(1).lower()
        sign_info = SIGN_MAP.get(sign_en)
        if not sign_info:
            continue

        content = entry.get("description", entry.get("summary", ""))
        lucky = extract_lucky_number(content)

        results[sign_en] = SignHoroscope(
            sign_key=sign_en,
            sign_zh=sign_info["zh"],
            sign_en=sign_info["en"],
            title=title.strip(),
            content=content.strip(),
            lucky_number=lucky,
            pub_date=entry.get("published", None),
        )
    return results


def parse_clickastro(feed: Any) -> dict[str, SignHoroscope]:
    """解析 ClickAstro RSS，格式：Aries Horoscope May 1 2026"""
    results: dict[str, SignHoroscope] = {}
    for entry in feed.entries:
        title = entry.title or ""
        sign_match = re.match(r"(\w+)\s+Horoscope", title, re.IGNORECASE)
        if not sign_match:
            continue
        sign_en = sign_match.group(1).lower()
        sign_info = SIGN_MAP.get(sign_en)
        if not sign_info:
            continue

        content = entry.get("description", entry.get("summary", ""))
        lucky = extract_lucky_number(content)

        results[sign_en] = SignHoroscope(
            sign_key=sign_en,
            sign_zh=sign_info["zh"],
            sign_en=sign_info["en"],
            title=title.strip(),
            content=content.strip(),
            lucky_number=lucky,
            pub_date=entry.get("published", None),
        )
    return results


def signs_to_dict(signs: dict[str, SignHoroscope]) -> dict[str, dict[str, Any]]:
    return {k: asdict(v) for k, v in signs.items()}


# --- TianAPI 抓取 ---

TIANAPI_SIGN_NAMES: dict[str, str] = {
    "aries": "aries", "taurus": "taurus", "gemini": "gemini",
    "cancer": "cancer", "leo": "leo", "virgo": "virgo",
    "libra": "libra", "scorpio": "scorpio", "sagittarius": "sagittarius",
    "capricorn": "capricorn", "aquarius": "aquarius", "pisces": "pisces",
}


def fetch_tianapi_single(sign_en: str) -> dict[str, Any] | None:
    """调用 TianAPI 获取单个星座运势，返回标准化 dict"""
    params = {"key": TIANAPI_KEY, "astro": sign_en}
    resp = requests.get(TIANAPI_BASE, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        return None

    # TianAPI 返回格式: result.list[] = [{type, content}, ...]
    result = data.get("result", {})
    items: dict[str, str] = {}
    for item in result.get("list", []):
        items[item["type"]] = item["content"]

    # 提取评分后缀（如 "70%" → 70）
    def strip_pct(s: str) -> int:
        return int(s.replace("%", "").strip()) if s else 0

    return {
        "all": items.get("今日概述", ""),
        "all_num": 0,  # 概述无分数
        "love": "",
        "love_num": strip_pct(items.get("爱情指数", "0")),
        "work": "",
        "work_num": strip_pct(items.get("工作指数", "0")),
        "money": "",
        "money_num": strip_pct(items.get("财运指数", "0")),
        "health": "",
        "health_num": strip_pct(items.get("健康指数", "0")),
        "color": items.get("幸运颜色", ""),
        "number": int(items.get("幸运数字", "0")),
        "qfriend": items.get("贵人星座", ""),
        "summary": items.get("今日概述", ""),
        "date": data.get("date", result.get("date", "")),
    }


def fetch_tianapi_all() -> dict[str, SignHoroscope]:
    """调用 TianAPI 获取全部 12 星座运势（逐星座请求，间隔 1s 避免限流）"""
    results: dict[str, SignHoroscope] = {}
    for sign_en in SIGN_MAP:
        try:
            result = fetch_tianapi_single(sign_en)
            if result and result.get("summary"):
                scores = []
                key_map = {"爱情": "love_num", "工作": "work_num", "财运": "money_num", "健康": "health_num"}
                for label in ["爱情", "工作", "财运", "健康"]:
                    s = result.get(key_map[label], 0)
                    scores.append(f"{label}：{s}%")

                content_parts = [
                    f"📊 {'  '.join(scores)}",
                    f"💬 {result['summary']}",
                ]
                if result.get("color"):
                    content_parts.append(f"🎨 幸运色：{result['color']}")
                if result.get("qfriend"):
                    content_parts.append(f"🤝 贵人星座：{result['qfriend']}")

                sign_info = SIGN_MAP[sign_en]
                results[sign_en] = SignHoroscope(
                    sign_key=sign_en,
                    sign_zh=sign_info["zh"],
                    sign_en=sign_info["en"],
                    title=f"{sign_info['zh']}今日运势",
                    content="\n".join(content_parts),
                    lucky_number=result.get("number"),
                    pub_date=result.get("date", ""),
                )
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ TianAPI {sign_en}: {e}")
            continue
    return results


# --- 抓取主流程 ---

def fetch_feed(url: str) -> Any:
    """抓取并解析 RSS feed"""
    resp = requests.get(url, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (compatible; HoroscopeFetcher/1.0)",
    })
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def fetch_all() -> DailyReport:
    now = datetime.now(BEIJING_TZ)
    report = DailyReport(
        date=now.strftime("%Y-%m-%d"),
        fetched_at=now.isoformat(),
    )

    # TianAPI 中文来源（优先）
    if TIANAPI_KEY:
        try:
            tianapi_signs = fetch_tianapi_all()
            report.sources["tianapi"] = {
                "name": "TianAPI（天聚数行）",
                "feed_url": TIANAPI_BASE,
                "fetch_ok": len(tianapi_signs) > 0,
                "error": None if len(tianapi_signs) == 12 else f"仅获取 {len(tianapi_signs)}/12 星座",
                "signs": signs_to_dict(tianapi_signs),
            }
        except Exception as e:
            report.sources["tianapi"] = {
                "name": "TianAPI（天聚数行）",
                "feed_url": TIANAPI_BASE,
                "fetch_ok": False,
                "error": str(e),
                "signs": {},
            }

    parsers = {
        "astrosage": ("AstroSage", parse_astrosage),
        "clickastro": ("ClickAstro", parse_clickastro),
    }

    for source_key, (source_name, parser_fn) in parsers.items():
        feed_url = RSS_FEEDS[source_key]
        try:
            feed = fetch_feed(feed_url)
            signs = parser_fn(feed)
            report.sources[source_key] = {
                "name": source_name,
                "feed_url": feed_url,
                "fetch_ok": True,
                "error": None,
                "signs": signs_to_dict(signs),
            }
        except Exception as e:
            report.sources[source_key] = {
                "name": source_name,
                "feed_url": feed_url,
                "fetch_ok": False,
                "error": str(e),
                "signs": {},
            }

    return report


def save_report(report: DailyReport) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"horoscope_{report.date}.json"
    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    # 同时更新 latest.json 软链式的快捷文件
    latest_path = OUTPUT_DIR / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, ensure_ascii=False, indent=2)

    return filepath


def main() -> None:
    print(f"[{datetime.now(BEIJING_TZ).isoformat()}] 开始抓取星座运势...")
    report = fetch_all()

    for key, src in report.sources.items():
        status = "✅" if src["fetch_ok"] else "❌"
        sign_count = len(src["signs"])
        print(f"  {status} {src['name']}: {sign_count}/12 星座")
        if src["error"]:
            print(f"      错误: {src['error']}")

    filepath = save_report(report)
    print(f"📁 已保存: {filepath}")
    print(f"📁 最新:   {OUTPUT_DIR / 'latest.json'}")


if __name__ == "__main__":
    main()
