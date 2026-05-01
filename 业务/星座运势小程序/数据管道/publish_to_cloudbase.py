"""发布星座运势数据到微信云开发数据库

通过腾讯云 API 网关将转换后的运势数据写入云开发 NoSQL 数据库。
支持 --dry-run 模式仅验证不写入。
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

BEIJING_TZ = timezone(timedelta(hours=8))

PIPELINE_DIR = Path(__file__).resolve().parent
MP_OUTPUT_DIR = PIPELINE_DIR / "output"
DEFAULT_INPUT = MP_OUTPUT_DIR / "latest.json"


@dataclass
class PublishResult:
    date: str
    published_signs: int
    skipped: int
    errors: list[dict[str, str]]


def load_mp_data(path: Path | None = None) -> dict[str, Any]:
    filepath = path or DEFAULT_INPUT
    if not filepath.exists():
        raise FileNotFoundError(f"小程序格式数据未找到: {filepath}\n请先运行 transform_horoscope.py")
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def format_for_cloudbase(data: dict[str, Any]) -> list[dict[str, Any]]:
    """将运势数据格式化为云开发数据库文档列表

    每个星座一条文档，结构适配云开发 NoSQL。
    """
    date_str = data["date"]
    documents: list[dict[str, Any]] = []

    for sign_key, sign in data["signs"].items():
        doc = {
            "_id": f"{date_str}_{sign_key}",
            "date": date_str,
            **sign,
        }
        documents.append(doc)

    return documents


def format_daily_meta(data: dict[str, Any]) -> dict[str, Any]:
    """生成 daily_meta 单例文档"""
    return {
        "_id": "current",
        "date": data["date"],
        "generated_at": data["generated_at"],
        "sign_count": len(data["signs"]),
    }


def publish(documents: list[dict[str, Any]], meta: dict[str, Any],
            env_id: str, api_key: str | None = None) -> PublishResult:
    """通过云开发 HTTP API 推送数据

    使用腾讯云 CloudBase Open API 的 database.insert 接口。
    需要 CLOUD_BASE_ENV_ID 和 CLOUD_BASE_API_KEY。
    """
    import urllib.request
    import urllib.error

    result = PublishResult(
        date=meta.get("date", ""),
        published_signs=0,
        skipped=0,
        errors=[],
    )

    base_url = f"https://{env_id}.service.tcloudbase.com"

    # 安全规则：文档级权限，仅创建者可写（实际由 API Key 控制）
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" if api_key else "",
    }

    # 批量写入 fortunes 集合
    for doc in documents:
        try:
            req = urllib.request.Request(
                f"{base_url}/api/v1/database/{env_id}/collections/fortunes/documents",
                data=json.dumps(doc).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    result.published_signs += 1
                else:
                    result.errors.append({
                        "sign": doc.get("sign_key", "unknown"),
                        "error": f"HTTP {resp.status}",
                    })
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            result.errors.append({
                "sign": doc.get("sign_key", "unknown"),
                "error": f"HTTP {e.code}: {error_body[:200]}",
            })
        except Exception as e:
            result.errors.append({
                "sign": doc.get("sign_key", "unknown"),
                "error": str(e),
            })

    # 更新 daily_meta 单例
    try:
        req = urllib.request.Request(
            f"{base_url}/api/v1/database/{env_id}/collections/daily_meta/documents/current",
            data=json.dumps(meta).encode("utf-8"),
            headers=headers,
            method="PUT",
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        result.errors.append({
            "sign": "daily_meta",
            "error": str(e),
        })

    return result


def validate(data: dict[str, Any]) -> list[str]:
    """验证数据完整性，返回问题列表"""
    issues: list[str] = []
    signs = data.get("signs", {})

    if not data.get("date"):
        issues.append("缺少 date 字段")

    if len(signs) != 12:
        issues.append(f"星座数量应为 12，当前 {len(signs)}")

    required_fields = ["sign_key", "sign_zh", "content", "rating", "lucky_number"]
    for sign_key, sign in signs.items():
        for field in required_fields:
            if field not in sign:
                issues.append(f"{sign_key}: 缺少 {field}")
            elif not sign[field] and field != "content":
                issues.append(f"{sign_key}: {field} 为空")

    return issues


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="发布运势数据到微信云开发")
    sub = parser.add_subparsers(dest="command")

    # validate 子命令
    v = sub.add_parser("validate", help="仅验证数据格式")
    v.add_argument("--input", type=Path, help="小程序格式 JSON，默认 latest.json")

    # publish 子命令
    p = sub.add_parser("publish", help="发布到云开发")
    p.add_argument("--input", type=Path, help="小程序格式 JSON，默认 latest.json")
    p.add_argument("--env-id", help="云开发环境 ID（或设置 CLOUD_BASE_ENV_ID）")
    p.add_argument("--api-key", help="云开发 API Key（或设置 CLOUD_BASE_API_KEY）")
    p.add_argument("--dry-run", action="store_true", help="验证但不实际发布")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    data = load_mp_data(args.input)

    # 验证
    issues = validate(data)
    if issues:
        print("❌ 数据验证失败:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)

    print(f"✅ 数据验证通过: {len(data['signs'])} 星座, 日期 {data['date']}")

    if args.command == "validate":
        return

    # 发布
    env_id = args.env_id or os.environ.get("CLOUD_BASE_ENV_ID", "")
    api_key = args.api_key or os.environ.get("CLOUD_BASE_API_KEY", "")

    if not env_id:
        print("❌ 需要设置 CLOUD_BASE_ENV_ID 或 --env-id")
        sys.exit(1)

    documents = format_for_cloudbase(data)
    meta = format_daily_meta(data)

    if args.dry_run:
        print(f"\n📋 Dry Run —— 将写入 {len(documents)} 条文档:")
        for doc in documents:
            print(f"  - {doc['_id']}: {doc['sign_zh']} (评分: {doc['rating']}/5)")
        print(f"  - daily_meta: {meta}")
        return

    print(f"\n🚀 开始发布到 {env_id}...")
    result = publish(documents, meta, env_id, api_key)

    print(f"✅ 发布完成: {result.published_signs}/{len(documents)} 条成功")
    if result.errors:
        print(f"❌ {len(result.errors)} 条失败:")
        for err in result.errors:
            print(f"  - {err['sign']}: {err['error']}")
    else:
        print("🎉 全部发布成功！")

    # 输出 JSON 结果（适配 CLI 规范）
    result_data = {
        "code": 200 if not result.errors else 201,
        "data": {
            "date": result.date,
            "published_signs": result.published_signs,
            "skipped": result.skipped,
            "errors": result.errors,
        },
    }
    print(json.dumps(result_data, ensure_ascii=False))


if __name__ == "__main__":
    main()
