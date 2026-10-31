# 点记 TapTally

> 小米手环 9 / 9 NFC 上的**对局计分**快应用（Xiaomi Vela / HyperOS）。
> 台球、乒乓、羽毛球、棋牌……面对面对局时，抬手点一下就能记分。

![封面](media/cover.png)

当前版本 **1.6.8**（versionCode 32）· 包名 `com.taptally.scoreboard` · [变更记录](docs/CHANGELOG.md)

---

## 一句话用法

上半区归上方选手、下半区归下方选手 —— **单击加分，长按减分，上滑两次归零并存档，右→左划看历史**。

---

## 手势总表

### 记分页（主界面）

| 手势 | 位置 | 结果 | 震动反馈 |
| --- | --- | --- | --- |
| 单击 | 任一半区 | 该方 **+1**，立即生效（不用等双击判定） | 短震 1 次 |
| 长按 | 任一半区 | 该方 **−1**；松手**不会**再补一次 +1（系统补发的点击被丢弃） | 短震 2 次 |
| 长按 | 任一半区且该方为 0 分 | 停在 **0**，不出现负数 | 短震 1 次 |
| 上滑 | 任意位置（第 1 次） | 中间窄缝显示「**再滑确认**」，**2.5 秒**内不动自动取消，比分不变 | 短震 1 次 |
| 上滑 | 任意位置（2.5 秒内第 2 次） | **存档并归零**：当前比分写入历史→回到 0:0，中缝短暂显示「已存 N 条」 | 短震 2 次 |
| 上滑 ×2 | 当前是 0:0 | 归零照旧，但**不产生记录**（0:0 不入库） | 短震 2 次 |
| 右→左划 | 任意位置 | 保存比分并**进入记分列表** | — |
| 左→右划 | 任意位置 | 保存比分并**退出应用**（等同系统返回） | — |

### 记分列表页

| 手势 | 位置 | 结果 | 震动反馈 |
| --- | --- | --- | --- |
| 单击 | 某条记录 | **恢复该条比分**，60ms 后自动返回记分页 | 短震 1 次 |
| 长按 | 某条记录 | **删除该条**，其余序号立刻重排，删掉的不会因为之后存分而复活 | 短震 1 次 |
| 左→右划 | 任意位置 | 返回记分页（比分保持当前值） | — |
| 上下划 | 列表区域 | 滚动（上限 5 条，正常一屏即可放下） | — |

### 隐藏操作（排查用，不影响日常使用）

| 手势 | 结果 |
| --- | --- |
| 长按记分页**中间窄缝** | 中缝显示 `192x490 pill-shaped v1.6.8 r5` —— 屏幕宽高、屏幕形状、版本号、已存记录数，4 秒后消失 |
| 长按历史页**标题「记录」** | 标题下方出现诊断行 `S89 F89 N5`（两个通道读到的字符数 / 内存条数），再长按一次收起 |

---

## 功能

### 记分页

- **上下双色分区**：上浅绿 `#7fd9b7`、下浅蓝 `#92cdf5`，两位选手的比分一眼分清
- **卡片贴边 + 大圆角**：胶囊形屏幕（手环 9/10）圆角 300px 且不留边距；圆屏留边、矩形屏走 52px，都不会露黑边
- **数字够大且不溢出**：字号同时受卡片宽度与高度约束（`min(卡宽/(0.6×位数), 卡高×0.74, 430)`），1~3 位数自动缩放
- **单击即 +1**：不等待双击判定，点击零延迟（早期版本为了区分双击要等 300ms，已废弃）
- **长按减分不重复**：长按后系统仍会补发一次点击，代码用 `longMark` 丢弃它，避免「先 −1 再加 1」
- **0 分锁底**：任何方式都不会减成负数
- **上滑两次才归零**：第一次只提示「再滑确认」，2.5 秒窗口，防误触清空
- **比分自动保存**：双通道持久化，退出应用、页面切换、手环重启都不丢
- **屏幕常亮**：对局中不黑屏，`onDestroy` 时释放

### 记分列表（历史）

- **右→左划进入**，保留**最近 5 局**，按时间**倒序**（最新在最上）
- 每条显示 **序号 · 色条 · 比分**，序号与比分字号随屏幕高度放大
- **单击恢复**：比分写回记分页并自动返回
- **长按删除**：立即删除并重排序号
- **0:0 不入库**：只有真正打过的局才记录
- 空列表显示「还没有记录」

### 兼容与自适应

- 通过 `device.getInfo()` 的 `screenWidth / screenHeight / screenShape` 推导设计高度、卡片高度、字号与圆角，同一份代码适配手环 9 / 9 NFC / 10 / 10 NFC、9 Pro / 10 Pro、红米手表 5·6、手表 S3/S4/S5 等机型，详见 [docs/兼容设备.md](docs/兼容设备.md)
- 机型参数不确定时，长按中缝读 `宽x高 形状` 回来即可核对

---

## 仓库结构

```
src/                     快应用源码（Vela ux 工程）
  manifest.json          快应用清单（包名、features、路由）
  app.ux                 应用生命周期（屏幕常亮）
  pages/index/index.ux   记分页：布局 + 手势 + 计分 + 自适应
  pages/history/history.ux  记分列表页
  common/store.js        数据层：比分与历史记录的双通道持久化
  common/logo.png        应用图标（手环应用列表显示，100×100、图形占 85%）
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
python scripts/check_syntax.py                     # 建议先跑，见下方「两个坑」
node node_modules/aiot-toolkit/lib/bin.js build --enable-jsc

cp dist/com.taptally.scoreboard.debug.<版本>.rpk "dist/点记-<版本>.rpk"   # 文件名带中文，安装队列里好认
```

产物：`dist/com.taptally.scoreboard.debug.<versionName>.rpk`

### 两个必须知道的坑

1. **必须带 `--enable-jsc`**：手环运行的是 Vela `.jsc` 字节码。手写 zip、或用手机版快应用的结构打包（`app.json` + 独立 `index.js`），装上去会**直接让手环重启** —— 缺编译产物与 `META-INF/CERT` 签名。
2. **aiot-toolkit 会静默吞掉语法错误**：某个模块写法有错时它不报错，而是把该模块编译成空模块（bundle 里变成 `"./src/common/store.js" () {}`），页面照常渲染但数据层全部失效，表现为「比分不保存、历史永远 0 条」。所以改动后先跑 `python scripts/check_syntax.py`（把 `.ux` 的 `<script>` 抽出来、去掉 `@system.*` import 后交给 `node --check`）。

`aiot release`（production 模式）需要自备 `sign/private.pem` + `sign/certificate.pem`；没有生产证书时只能用 development 模式的调试签名。

---

## 安装

1. 打开 [AstroBox](https://astrobox.online)，通过 BLE 连接手环（先在 AstroBox 里配对好 MAC 与 AuthKey）；
2. 「设备 → 安装队列」选择 `点记-<版本>.rpk`；
3. 覆盖安装即可。**图标有系统级缓存**，换图标后若列表里没变，先在应用列表里删掉「点记」再装一次；
4. 包名变更（如 `com.sports.scoreboard` → `com.taptally.scoreboard`）时新旧版本互不覆盖，需手动卸载旧的。

> 传输层的坑：网页端 `mibandinstall.0pen.top` 或自写 BLE 脚本常卡在 `Timeout waiting for mass packet ACK`；AstroBox 的 Windows / iOS 客户端是验证过能完整装完的路径。

---

## 设备与兼容

| 项 | 值 |
| --- | --- |
| 目标设备 | 小米手环 9 / 9 NFC（社区设备代号 `xmb9`，屏幕 192×490，pill-shaped） |
| 屏幕适配 | `device.getInfo()` 的 `screenWidth/screenHeight/screenShape` → 设计高度、卡片高、字号、圆角 |
| 已梳理机型 | 手环 9 / 9 NFC / 10 / 10 NFC、9 Pro / 10 Pro、红米手表 5·6、手表 S3/S4/S5 等，详见 [docs/兼容设备.md](docs/兼容设备.md) |
| 存储 key | 比分 `taptally_v1`；历史 `taptally_records_v1`（两者都镜像到 `internal://files/*.txt`） |
| 工具链 | aiot-toolkit 2.0.5 + @aiot-toolkit/jsc |
| 清单 features | system.router / configuration / vibrator / brightness / storage / file / device |

---

## 数据层设计（为什么这么写）

- **双通道**：`@system.storage` 与 `@system.file` 同时写、同时读，任一通道能解析出合法数据即可恢复；
- **版本戳**：落盘文本带毫秒时间戳前缀（`1759…|12-9-1759…;7-11-…`），读取时两个通道取版本戳更新的那份，晚写的操作必胜；
- **先读后写**：`addRecord` / `removeRecord` 都先 `loadRecords(force)` 回读磁盘再写。Vela 里**每个页面各持一份模块实例**，记分页的缓存可能是「删除前」的状态，直接写盘会把删掉的记录写回去；
- **不用追加日志**：1.5.0 曾用「只追加的日志 + 回读合并」，结果删除的条目被日志捞回来，1.6.4 起移除。

---

## 已知限制

- 历史**上限 5 条**，第 6 局会挤掉最早的一条；没有「撤销删除」
- 单边比分上限 **999**（安全阈值，避免字号缩到不可读）
- 没有联网、没有账号、没有排行榜；数据只在本机
- NFC 版与普通版功能完全一致，**未使用 NFC**（记分不需要碰一碰，如需要可加「碰一碰传比分」）

---

## 发布到 AstroBox 资源社区

社区源（OfficialV2）不解析本地 rpk 的名称与图标，只能通过官方索引收录：仓库里放 `manifest_v2.json` + `media/` + `downloads/`，再向 [AstroBox-Repo](https://github.com/AstralSightStudios/AstroBox-Repo) 提交 `tmp/<owner>/<repo>/resource.csv` + `request.json` 的 PR。

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
