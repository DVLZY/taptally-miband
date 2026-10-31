#-*- coding: utf-8 -*-
"""生成 AstroBox 资源社区的提交物（tmp/<owner>/<repo>/resource.csv + request.json）。

按 AstroBox-Repo 的 .github/scripts/resource_submissions.py 要求：
- PR 只能改 tmp/** 下的 resource.csv 与 request.json；
- 每个 PR 只允许一个 submission 目录（路径至少 tmp/a/b/ 三段）；
- resource.csv 必须与 index_v2.csv 同表头、且**恰好 1 行数据**；
- request.json 需要 {"schema_version": 1, "mode": "create"}。

用法：
    python publish/make_submission.py --out E:\\...\\_abx_submit --commit <repo commit sha>

生成结果：
    <out>/tmp/DVLZY/taptally/resource.csv
    <out>/tmp/DVLZY/taptally/request.json
"""
import argparse
import csv
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEADER = [
    "id", "name", "restype", "repo_owner", "repo_name", "repo_commit_hash",
    "icon", "cover", "tags", "device_vendors", "devices", "paid_type",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="输出的临时仓库根目录")
    ap.add_argument("--commit", required=True, help="发布文件所在的 commit（短哈希即可）")
    ap.add_argument("--owner", default="DVLZY")
    ap.add_argument("--repo", default="taptally-miband")
    args = ap.parse_args()

    manifest = json.load(io.open(os.path.join(ROOT, "manifest_v2.json"), encoding="utf-8"))
    item = manifest["item"]
    row = {
        "id": item["id"],
        "name": item["name"],
        "restype": item["restype"],
        "repo_owner": args.owner,
        "repo_name": args.repo,
        "repo_commit_hash": args.commit,
        "icon": item["icon"],
        "cover": item["cover"],
        "tags": "实用工具;计分;比分;台球;乒乓;羽毛球;棋牌;对局",
        "device_vendors": "xiaomi",
        "devices": ";".join(manifest["downloads"].keys()),
        "paid_type": "",
    }

    sub = os.path.join(args.out, "tmp", args.owner, "taptally")
    os.makedirs(sub, exist_ok=True)

    csv_path = os.path.join(sub, "resource.csv")
    with io.open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, lineterminator="\n")
        w.writeheader()
        w.writerow(row)
    print("wrote", csv_path)

    req_path = os.path.join(sub, "request.json")
    with io.open(req_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"schema_version": 1, "mode": "create"}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("wrote", req_path)


if __name__ == "__main__":
    main()
