#!/usr/bin/env bash
# 生成本地发布签名证书（自签 RSA-2048），供 `aiot release` 使用。
#
# 为什么需要它：aiot-toolkit 的 development 模式会用工具链**内置的调试证书**签名，
# 而 AstroBox 社区源明确不接收调试证书签名的快应用（内容规范 2.6.2）。
# production 模式只认项目下的 sign/private.pem 与 sign/certificate.pem（见
# @aiot-toolkit/aiotpack 的 SignUtil.getProjectSignConfig）。
#
# 用法：
#   bash scripts/gen_sign.sh          # 生成到 ./sign/
#   node node_modules/aiot-toolkit/lib/bin.js release
#
# 证书只用于给本应用签名，不入库（.gitignore 已忽略 sign/），换机器重新生成即可；
# 注意：同一资源的升级包必须用同一张证书签名，所以请把 sign/ 备份好。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/sign"

if [ -f "$OUT/private.pem" ] && [ -f "$OUT/certificate.pem" ]; then
  echo "sign/ 已存在，跳过：$OUT" >&2
  exit 0
fi

mkdir -p "$OUT"
openssl req -x509 -newkey rsa:2048 \
  -keyout "$OUT/private.pem" \
  -out "$OUT/certificate.pem" \
  -days 3650 -nodes \
  -subj "/C=CN/O=TapTally/CN=TapTally" \
  -addext "basicConstraints=critical,CA:FALSE"

echo "已生成："
ls -l "$OUT"
echo "下一步：node node_modules/aiot-toolkit/lib/bin.js release"
