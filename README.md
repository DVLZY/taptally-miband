# 点记 TapTally

> 小米手环 9 / 9 NFC 上的**对局计分**快应用（Xiaomi Vela / HyperOS）。
> 台球、乒乓、羽毛球、棋牌……面对面对局时，抬手点一下就记分。

![封面](media/cover.png)

当前版本 **1.6.5**（versionCode 29）· 包名 `com.taptally.scoreboard`

---

## 功能

**记分页**

- **上下双色分区**：上浅绿、下浅蓝，两位选手的比分一眼分清，卡片圆角 300px，贴边显示无黑边
- **单击 +1**：立即生效，短震一次，不用等
- **长按 −1**：短震一次；松手不会再补一次 +1（长按结束后系统补发的点击会被丢弃）
- **0 分锁底**：任何方式都不会减成负数
- **上滑两次归零**：第一次显示「再滑确认」，2.5 秒内再滑一次才清空，防误触
- **比分自动保存**：双通道持久化，退出重进、断电重启都还在
- **屏幕常亮**：对局中不黑屏，退出时释放
- **自适应字号**：1~3 位数按卡片尺寸自动缩放，从手环 9 到 Pro 到圆表都不溢出

**记分列表**

- **右→左划**进入，保留**最近 5 局**，按时间倒序（最新在最上）
- 每条显示 `序号 · 色条 · 比分`
- **单击**某条：恢复该比分并返回记分页
- **长按**某条：删除该条（删掉的不会因为之后存分而复活）
- **左→右划**返回记分页
- 0:0 不入库（只有真正打过的局才记录）

**其他**

- 长按记分页中间窄缝：显示 `宽x高 形状 版本 记录数`，换机型时用来核对参数
- 长按历史页标题：切换诊断行 `S/F/L/N`（存储字符数 / 内存条数），排查数据通道用

---

## 手势总表

| 页面 | 手势 | 结果 |
| --- | --- | --- |
| 记分页 | 单击半区 | +1 |
| 记分页 | 长按半区 | −1 |
| 记分页 | 上滑 ×2 | 存档并归零 |
| 记分页 | 右→左划 | 进入记分列表 |
| 记分页 | 左→右划 | 退出应用 |
| 历史页 | 单击条目 | 恢复比分并返回 |
| 历史页 | 长按条目 | 删除该条 |
| 历史页 | 左→右划 | 返回记分页 |

---

## 仓库结构

```
src/                     快应用源码（Vela ux 工程）
  manifest.json          快应用清单（包名、features、路由）
  app.ux                 应用生命周期（屏幕常亮）
  pages/index/index.ux   记分页：布局 + 手势 + 计分
  pages/history/history.ux  记分列表页
  common/store.js        数据层：比分与历史记录的双通道持久化
  common/logo.png        应用图标（手环应用列表里显示，100×100）
package.json             构建脚本与工具链依赖
scripts/check_syntax.py  构建前语法自检（工具链会静默吞掉语法错误）
manifest_v2.json         AstroBox 资源社区条目元数据（v2 格式）
media/                   社区物料：icon 192 / cover 1200×800 / preview
downloads/               社区分发的 release rpk
publish/                 物料生成脚本、投稿生成脚本与发布说明
docs/                    验证清单、兼容设备、变更日志
design/                  UI 方案与图标对比图（PIL 生成）
```

> 根目录 `manifest_v2.json` 是给 **AstroBox 资源社区**用的条目元数据；快应用真正的清单在 `src/manifest.json`，两者不是一回事。

---

## 构建

```bash
pnpm install --registry=https://registry.npmjs.org
python scripts/check_syntax.py                     # 建议先跑，见下方「坑」
node node_modules/aiot-toolkit/lib/bin.js build --enable-jsc

cp dist/com.taptally.scoreboard.debug.<版本>.rpk "dist/点记-<版本>.rpk"   # 文件名带中文，安装队列里好认
```

产物：`dist/com.taptally.scoreboard.debug.<versionName>.rpk`

### 两个必须知道的坑

1. **必须带 `--enable-jsc`**：手环运行的是 Vela `.jsc` 字节码。手写 zip、或用手机版快应用的结构打包（`app.json` + 独立 `index.js`），装上去会**直接让手环重启** —— 因为缺编译产物与 `META-INF/CERT` 签名。
2. **aiot-toolkit 会静默吞掉语法错误**：某个模块写法有错时它不报错，而是把这个模块编译成空模块（bundle 里变成 `"./src/common/store.js" () {}`），页面照常渲染但数据层全部失效，表现是「比分不保存、历史永远 0 条」。所以改动后先跑 `python scripts/check_syntax.py`（它把 `.ux` 里的 `<script>` 抽出来，去掉 `@system.*` import 后交给 `node --check`）。

`aiot release`（production 模式）需要自备 `sign/private.pem` + `sign/certificate.pem`；没有生产证书时只能用 development 模式的调试签名打包。

---

## 安装

1. 打开 [AstroBox](https://astrobox.online)，通过 BLE 连接手环（小米手环 9 NFC 的 MAC 与 AuthKey 需先在 AstroBox 里配对）；
2. 「设备 → 安装队列」选择 `点记-<版本>.rpk`；
3. 覆盖安装即可；**图标有系统级缓存**，换图标后如果列表里没变，先在应用列表里删掉「点记」再装一次；
4. 包名变更（例如从 `com.sports.scoreboard` 改到 `com.taptally.scoreboard`）时，新旧版本互不覆盖，需手动卸载旧的。

> 传输层的坑：走网页端 `mibandinstall.0pen.top` 或自写 BLE 脚本经常卡在 `Timeout waiting for mass packet ACK`；AstroBox 的 Windows / iOS 客户端是验证过能装完的路径。

---

## 设备与兼容

| 项 | 值 |
| --- | --- |
| 目标设备 | 小米手环 9 / 9 NFC（社区设备代号 `xmb9`，屏幕 192×490，pill-shaped） |
| 屏幕适配 | 由 `device.getInfo()` 的 `screenWidth/screenHeight/screenShape` 推导设计高度与卡片高度，按形状选圆角 |
| 已梳理机型 | 手环 9 / 9 NFC / 10 / 10 NFC、9 Pro / 10 Pro、红米手表 5·6、手表 S3/S4/S5 等，详见 [docs/兼容设备.md](docs/兼容设备.md) |
| 存储 key | 比分 `taptally_v1`，历史 `taptally_records_v1`（同时镜像到 `internal://files/*.txt`） |
| 工具链 | aiot-toolkit 2.0.5 + @aiot-toolkit/jsc |
| 清单 features | system.router / configuration / vibrator / brightness / storage / file / device |

---

## 数据层设计（为什么这么写）

- **双通道**：`@system.storage` 与 `@system.file` 同时写、同时读，任一通道能解析出合法数据即可恢复；
- **版本戳**：落盘文本带毫秒时间戳前缀（`1759…|12-9-1759…;7-11-…`），读取时两个通道取版本戳更新的那份，晚写的操作必胜；
- **先读后写**：`addRecord` / `removeRecord` 都先 `loadRecords(force)` 回读磁盘再写。Vela 里**每个页面各持一份模块实例**，记分页的缓存可能是「删除前」的状态，直接写盘会把删掉的记录写回去；
- **不再用追加日志**：1.5.0 曾用「只追加的日志 + 回读合并」，结果删除的条目会被日志捞回来，1.6.4 起移除。

---

## 发布到 AstroBox 资源社区

社区源（OfficialV2）不解析本地 rpk 的名称与图标，只能通过官方索引收录：仓库里放 `manifest_v2.json` + `media/` + `downloads/`，再向 [AstroBox-Repo](https://github.com/AstralSightStudios/AstroBox-Repo) 提交 `tmp/<owner>/<repo>/resource.csv` + `request.json` 的 PR。

生成投稿物：

```bash
python publish/make_submission.py --out <输出目录> --commit <仓库 commit>
```

详见 [publish/发布说明.md](publish/发布说明.md)。

---

## 文档

- [docs/验证清单.md](docs/验证清单.md) — 真机验收步骤（30 项）
- [docs/兼容设备.md](docs/兼容设备.md) — 机型矩阵与自适应公式
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — 版本变更记录

## 许可

[MIT](LICENSE)
