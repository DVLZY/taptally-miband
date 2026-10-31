"""构建前语法自检。

背景：aiot-toolkit 打包时如果某个模块语法有错，**不会报错**，而是把它编译成
空模块（bundle 里变成 `"./src/common/store.js" () {}`），于是页面照常渲染、
但所有数据读写直接静默失效 —— 这个坑排查了整整一轮才知道。
所以每次 build 之前，先把所有 JS 抽出来用 node --check 过一遍。
"""
import io
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')


def strip_imports(code: str) -> str:
    # @system.* 是平台注入的模块，node 不认，检查语法时去掉
    return re.sub(r"^\s*import\s+.*?from\s+'@system[^']*'\s*$", '', code, flags=re.M)


def script_of(path: str):
    text = io.open(path, encoding='utf-8').read()
    m = re.search(r'<script>(.*?)</script>', text, re.S)
    return m.group(1) if m else None


def check(name: str, code: str) -> bool:
    tmp = os.path.join(tempfile.gettempdir(), 'taptally_chk.mjs')
    io.open(tmp, 'w', encoding='utf-8').write(strip_imports(code))
    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
    if r.returncode != 0:
        print('FAIL', name)
        print(r.stderr.strip()[:900])
        return False
    print('ok  ', name)
    return True


def main() -> int:
    targets = []
    for base, _dirs, files in os.walk(SRC):
        for f in files:
            p = os.path.join(base, f)
            rel = os.path.relpath(p, ROOT)
            if f.endswith('.ux'):
                code = script_of(p)
                if code:
                    targets.append((rel, code))
            elif f.endswith('.js'):
                targets.append((rel, io.open(p, encoding='utf-8').read()))
    ok = all([check(n, c) for n, c in targets])
    if not ok:
        print('语法检查未通过，先修掉再 build —— 否则打出来的包会静默丢逻辑')
        return 1
    print('全部通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
