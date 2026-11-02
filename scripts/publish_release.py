#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""发布「点记」到 GitHub：推送 main + 创建 Release 并上传 rpk 附件。

没有 gh CLI，用 GitHub REST API；token 从 Git Credential Manager 静默读取
（`git credential fill`，与 git push 用的是同一份凭据）。

用法：
    python scripts/publish_release.py                 # 用 src/manifest.json 的版本号
    python scripts/publish_release.py --retry 20      # 网络不稳时重试 20 次，每次间隔 30 秒
    python scripts/publish_release.py --dry-run       # 只检查环境与待办项，不写任何东西

约定：
  * 附件名必须是 ASCII（GitHub 会把中文文件名截掉前缀），所以上传 dist/TapTally-<版本>.rpk
  * Release 已存在则跳过创建、只在缺附件时补传
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER, REPO = "DVLZY", "taptally-miband"
API = "https://api.github.com"


def sh(args, **kw):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, **kw)


def manifest_version():
    with open(os.path.join(ROOT, "src", "manifest.json"), encoding="utf-8") as f:
        m = json.load(f)
    return m["versionName"], m["versionCode"]


def asset_name(version):
    return "TapTally-%s.rpk" % version


def asset_path(version):
    return os.path.join(ROOT, "dist", asset_name(version))


def ensure_ascii_asset(version):
    """release 产物叫 com.taptally.scoreboard.release.<ver>.rpk，复制一份 ASCII 名字的。"""
    src = os.path.join(ROOT, "dist", "com.taptally.scoreboard.release.%s.rpk" % version)
    dst = asset_path(version)
    if not os.path.exists(src):
        sys.exit("找不到产物：%s（先跑 release --enable-jsc）" % src)
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
        with open(src, "rb") as fi, open(dst, "wb") as fo:
            fo.write(fi.read())
        print("已准备附件：dist/%s (%d B)" % (asset_name(version), os.path.getsize(dst)))
    return dst


def token():
    env = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if env:
        return env.strip()
    p = sh(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n")
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1].strip()
    sys.exit("拿不到 token：git credential fill 无输出（先手动 push 一次让 GCM 记住凭据）")


def api(path, tok, data=None, method=None, raw=None, content_type="application/json"):
    url = API + path
    body = None
    headers = {
        "Authorization": "Bearer " + tok,
        "Accept": "application/vnd.github+json",
        "User-Agent": "taptally-publish",
    }
    if raw is not None:
        body = raw
        headers["Content-Type"] = content_type
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method or ("POST" if body else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            text = r.read().decode() or "{}"
            return r.status, json.loads(text)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version")
    ap.add_argument("--tag")
    ap.add_argument("--notes")
    ap.add_argument("--retry", type=int, default=1, help="失败重试次数")
    ap.add_argument("--interval", type=int, default=30, help="重试间隔秒")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    version, code = manifest_version()
    version = args.version or version
    tag = args.tag or ("v" + version)
    notes_path = args.notes or os.path.join(ROOT, "docs", "release-notes-%s.md" % version)
    notes = ""
    if os.path.exists(notes_path):
        with open(notes_path, encoding="utf-8") as f:
            notes = f.read()
    else:
        notes = "点记 %s（versionCode %d）" % (version, code)

    dist = ensure_ascii_asset(version)
    print("版本 %s / versionCode %s / tag %s / 附件 %s" % (version, code, tag, os.path.basename(dist)))

    # 1) 推 main
    ahead = sh(["git", "rev-list", "--count", "origin/main..HEAD"]).stdout.strip() or "?"
    print("待推送提交数：%s" % ahead)
    if args.dry_run:
        print("dry-run：跳过 push 与 Release")
        return

    for attempt in range(1, max(1, args.retry) + 1):
        print("—— 第 %d 次尝试 ——" % attempt)
        pushed = sh(["git", "push", "origin", "main"])
        if pushed.returncode != 0:
            print("push 失败：%s" % (pushed.stderr.strip().splitlines() or [""])[-1])
            if attempt < args.retry:
                time.sleep(args.interval)
            continue
        print("push 成功")

        tok = token()
        st, rel = api("/repos/%s/%s/releases/tags/%s" % (OWNER, REPO, tag), tok)
        if st == 200:
            print("Release %s 已存在" % tag)
        else:
            st, rel = api(
                "/repos/%s/%s/releases" % (OWNER, REPO),
                tok,
                {"tag_name": tag, "name": "点记 TapTally %s" % version,
                 "body": notes, "draft": False, "prerelease": False},
            )
            if st not in (200, 201):
                print("创建 Release 失败 %s：%s" % (st, rel))
                return
            print("Release 已创建：%s" % rel.get("html_url"))

        upload = rel.get("upload_url", "").split("{")[0]
        names = [a["name"] for a in rel.get("assets", [])]
        if os.path.basename(dist) in names:
            print("附件已存在，跳过上传")
        else:
            with open(dist, "rb") as f:
                payload = f.read()
            st, up = api(
                upload.replace("https://api.github.com", "") + "?name=" + urllib.request.quote(os.path.basename(dist)),
                tok, raw=payload, content_type="application/octet-stream",
            )
            print("附件上传 %s：%s" % (st, up if st >= 300 else "ok %d B" % len(payload)))
        print("完成：https://github.com/%s/%s/releases/tag/%s" % (OWNER, REPO, tag))
        return

    sys.exit("重试 %d 次仍失败（网络不通）" % args.retry)


if __name__ == "__main__":
    main()
