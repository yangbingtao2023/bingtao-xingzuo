"""将转换后的运势数据推送到 CloudBase 数据库

使用 tcb CLI（需先 tcb login）。
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BEIJING_TZ = timezone(timedelta(hours=8))
ENV_ID = os.environ.get("TCB_ENV_ID", "yangbingtao-d1gmeitgw3a00bb90")
PIPELINE_DIR = Path(__file__).resolve().parent


def load_data(date_str: str | None = None) -> dict:
    date_str = date_str or datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
    filepath = PIPELINE_DIR / "output" / f"mp_fortunes_{date_str}.json"
    if not filepath.exists():
        raise FileNotFoundError(f"数据文件不存在: {filepath}")
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def run_tcb(command: str) -> bool:
    """执行 tcb db nosql execute 命令"""
    result = subprocess.run(
        ["npx", "tcb", "db", "nosql", "execute",
         "--command", command, "--env-id", ENV_ID],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode == 0 and '"ok"' in result.stdout


def upload(data: dict) -> None:
    """主上传流程"""
    date_str = data["date"]

    # 构建文档列表
    docs = []
    for sign_key, sign in data["signs"].items():
        docs.append({
            "_id": f"{date_str}_{sign_key}",
            "date": date_str,
            "sign_key": sign["sign_key"],
            "sign_zh": sign["sign_zh"],
            "sign_en": sign["sign_en"],
            "date_range": sign["date_range"],
            "element": sign["element"],
            "planet": sign["planet"],
            "lucky_number": sign["lucky_number"],
            "lucky_color": sign["lucky_color"],
            "rating": sign["rating"],
            "content": sign["content"],
            "tags": sign["tags"],
        })

    # 删除当日旧数据
    del_cmd = json.dumps([{
        "TableName": "fortunes",
        "CommandType": "DELETE",
        "Command": json.dumps({
            "delete": "fortunes",
            "deletes": [{"q": {"date": date_str}, "limit": 0}],
        }),
    }])
    if run_tcb(del_cmd):
        print(f"  🗑️  已清除旧数据")
    else:
        print(f"  ⚠️  清除旧数据失败，继续插入...")

    # 插入新数据
    ins_cmd = json.dumps([{
        "TableName": "fortunes",
        "CommandType": "INSERT",
        "Command": json.dumps({"insert": "fortunes", "documents": docs}),
    }])
    if run_tcb(ins_cmd):
        print(f"  ✅ fortunes: {len(docs)} 条成功")
    else:
        print("  ❌ 写入失败")
        sys.exit(1)

    # 更新 daily_meta
    meta_cmd = json.dumps([{
        "TableName": "daily_meta",
        "CommandType": "UPDATE",
        "Command": json.dumps({
            "update": "daily_meta",
            "updates": [{
                "q": {"_id": "current"},
                "u": {"$set": {
                    "date": date_str,
                    "generated_at": data.get("generated_at", ""),
                }},
            }],
        }),
    }])
    if run_tcb(meta_cmd):
        print(f"  ✅ daily_meta 已更新")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="推送运势数据到 CloudBase")
    parser.add_argument("--date", help="日期 YYYY-MM-DD，默认今天")
    parser.add_argument("--dry-run", action="store_true", help="仅验证不推送")
    args = parser.parse_args()

    data = load_data(args.date)
    print(f"📦 {len(data['signs'])} 星座, 日期 {data['date']}")

    if args.dry_run:
        print("  ✅ 格式验证通过")
        return

    upload(data)
    print("🎉 完成")


if __name__ == "__main__":
    main()
