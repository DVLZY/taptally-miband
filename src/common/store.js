// 数据层：比分与历史记录
// 双通道持久化：@system.storage（偏好存储）+ @system.file（应用私有文件）
//
// 关键设计（1.6.4 起）：
//   1) 所有数据在模块内有一份**内存缓存**，写入先改缓存（同步生效）再落盘；
//   2) 落盘带**版本戳**（毫秒时间戳前缀），读取时两个通道谁的时间戳新就用谁 ——
//      这样「删除后又被旧数据捞回来」的情况不会发生；
//   3) 放弃 1.5.0 引入的「追加日志」通道：真机上 append 不可靠，且删除后
//      再合并日志会把删掉的条目重新捞回来（用户 1.6.3 实测复现）。
//      两个通道都写、读取时按版本戳取最新，已经足够。

import storage from '@system.storage'
import file from '@system.file'

const SCORE_KEY = 'taptally_v1'
const SCORE_FILE = 'internal://files/taptally-score.txt'
const RECORD_KEY = 'taptally_records_v1'
const RECORD_FILE = 'internal://files/taptally-records.txt'

// 版本戳与记录列表之间的分隔符（老数据没有这个前缀，按版本 0 处理）
const VER_SEP = '|'

export const MAX_RECORDS = 5

// 版本号（页面里显示，用来确认手环上跑的到底是哪一版）
export const APP_VERSION = '1.9.1'

// 内存缓存
let scoreCache = null // { t, b }
let recordCache = null // [{ t, b, ts }]
let recordStamp = 0 // 当前记录列表的版本戳

function now() {
  try {
    return Date.now() || 0
  } catch (e) {
    return 0
  }
}

// 兼容 success 回调的多种形态：原始字符串 / {value} / {data}
function pick(data) {
  if (data === undefined || data === null) return null
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    if (data.value !== undefined && data.value !== null) return String(data.value)
    if (data.data !== undefined && data.data !== null) return String(data.data)
    return null
  }
  return String(data)
}

function writeBoth(key, uri, text) {
  try {
    storage.set({ key: key, value: text })
  } catch (e) {}
  try {
    file.writeText({ uri: uri, text: text })
  } catch (e) {}
}

function readBoth(key, uri, cb) {
  let pending = 2
  const out = { s: null, f: null }
  const done = function () {
    pending--
    if (pending === 0) cb(out)
  }
  try {
    storage.get({
      key: key,
      success: function (data) {
        out.s = pick(data)
        done()
      },
      fail: function () {
        done()
      }
    })
  } catch (e) {
    done()
  }
  try {
    file.readText({
      uri: uri,
      success: function (data) {
        out.f = data && data.text ? String(data.text) : null
        done()
      },
      fail: function () {
        done()
      }
    })
  } catch (e) {
    done()
  }
}

function later(fn) {
  try {
    setTimeout(fn, 0)
  } catch (e) {
    fn()
  }
}

// ---------- 比分 ----------
// "12-9" -> { t:12, b:9 }；非法返回 null
export function parseScore(raw) {
  if (raw === undefined || raw === null) return null
  const s = String(raw).trim()
  if (!s) return null
  const parts = s.split('-')
  if (parts.length !== 2) return null
  const t = parseInt(parts[0], 10)
  const b = parseInt(parts[1], 10)
  if (isNaN(t) || isNaN(b)) return null
  if (t < 0 || b < 0 || t > 999 || b > 999) return null
  return { t: t, b: b }
}

export function saveScore(t, b) {
  scoreCache = { t: t, b: b }
  writeBoth(SCORE_KEY, SCORE_FILE, t + '-' + b)
}

export function loadScore(cb, force) {
  if (scoreCache && !force) {
    const c = { t: scoreCache.t, b: scoreCache.b }
    later(function () {
      cb(c)
    })
    return
  }
  readBoth(SCORE_KEY, SCORE_FILE, function (out) {
    const sc = parseScore(out.s) || parseScore(out.f)
    // force 回读时：磁盘上读不到就保留缓存，绝不把已有比分清掉
    if (sc) scoreCache = sc
    cb(scoreCache ? { t: scoreCache.t, b: scoreCache.b } : null)
  })
}

// ---------- 历史记录 ----------
// 单条格式 "上-下-时间戳"，多条用分号；整体再加 "版本戳|" 前缀
function parseList(body) {
  if (!body) return null
  const s = String(body).trim()
  if (!s) return null
  // 老版本（1.1.0~1.3.1）整份存的是 JSON 数组 [[t,b,ts],…]：
  // 升级后必须能读回来，否则用户的历史记录会静默清空
  if (s.charAt(0) === '[') {
    try {
      const arr = JSON.parse(s)
      if (arr && typeof arr.length === 'number') {
        const legacy = []
        for (let i = 0; i < arr.length; i++) {
          const row = arr[i]
          if (!row || typeof row.length !== 'number' || row.length < 2) continue
          const lt = parseInt(row[0], 10)
          const lb = parseInt(row[1], 10)
          const lts = row.length > 2 ? parseInt(row[2], 10) : 0
          if (isNaN(lt) || isNaN(lb)) continue
          if (lt < 0 || lb < 0 || lt > 999 || lb > 999) continue
          legacy.push({ t: lt, b: lb, ts: isNaN(lts) ? 0 : lts })
        }
        return legacy
      }
    } catch (e) {}
    return null
  }
  const segs = s.split(';')
  const out = []
  for (let i = 0; i < segs.length; i++) {
    const seg = String(segs[i]).trim()
    if (!seg) continue
    const p = seg.split('-')
    if (p.length < 2) continue
    const t = parseInt(p[0], 10)
    const b = parseInt(p[1], 10)
    const ts = p.length > 2 ? parseInt(p[2], 10) : 0
    if (isNaN(t) || isNaN(b)) continue
    if (t < 0 || b < 0 || t > 999 || b > 999) continue
    out.push({ t: t, b: b, ts: isNaN(ts) ? 0 : ts })
  }
  return out
}

// 拆版本戳前缀：老数据没有前缀，版本戳记 0
function unpack(raw) {
  if (raw === undefined || raw === null) return null
  const s = String(raw).trim()
  if (!s) return null
  const i = s.indexOf(VER_SEP)
  if (i < 0) return { stamp: 0, list: parseList(s) }
  const head = s.slice(0, i)
  const stamp = parseInt(head, 10)
  return { stamp: isNaN(stamp) ? 0 : stamp, list: parseList(s.slice(i + 1)) }
}

function pack(list, stamp) {
  const segs = []
  for (let i = 0; i < list.length; i++) {
    segs.push(list[i].t + '-' + list[i].b + '-' + (list[i].ts || 0))
  }
  return String(stamp) + VER_SEP + segs.join(';')
}

function clone(list) {
  const out = []
  for (let i = 0; i < list.length; i++) out.push({ t: list[i].t, b: list[i].b, ts: list[i].ts || 0 })
  return out
}

// 按 (t,b,ts) 去重 + 时间倒序 + 截断
function normalize(lists) {
  const seen = {}
  const out = []
  for (let i = 0; i < lists.length; i++) {
    const arr = lists[i]
    if (!arr) continue
    for (let k = 0; k < arr.length; k++) {
      const r = arr[k]
      const key = r.t + '-' + r.b + '-' + (r.ts || 0)
      if (seen[key]) continue
      seen[key] = 1
      out.push({ t: r.t, b: r.b, ts: r.ts || 0 })
    }
  }
  out.sort(function (a, b) {
    return (b.ts || 0) - (a.ts || 0)
  })
  return out.slice(0, MAX_RECORDS)
}

// 落盘：两个通道写同一份带新版本戳的文本
// 版本戳必须**严格递增**：同一毫秒内两个页面各写一次时，若戳相同，
// loadRecords 会走「戳相等则合并两份」的分支，删除掉的条目可能被另一份加回来。
function flush() {
  const t = now()
  recordStamp = t > recordStamp ? t : recordStamp + 1
  const text = pack(recordCache || [], recordStamp)
  writeBoth(RECORD_KEY, RECORD_FILE, text)
}

export function loadRecords(cb, force) {
  if (recordCache && !force) {
    const c = clone(recordCache)
    later(function () {
      cb(c)
    })
    return
  }
  readBoth(RECORD_KEY, RECORD_FILE, function (out) {
    const a = unpack(out.s)
    const b = unpack(out.f)
    let chosen = null
    if (a && b) {
      if (a.stamp > b.stamp) chosen = a
      else if (b.stamp > a.stamp) chosen = b
      else chosen = { stamp: a.stamp, list: normalize([a.list, b.list]) }
    } else {
      chosen = a || b
    }
    if (chosen && (chosen.stamp > recordStamp || !recordCache)) {
      recordCache = normalize([chosen.list])
      recordStamp = chosen.stamp
    }
    if (!recordCache) recordCache = []
    cb(clone(recordCache))
  })
}

export function saveRecords(list) {
  recordCache = normalize([list])
  flush()
}

// 新增一条：**先强制回读磁盘拿到最新列表**，再追加并落盘。
// 为什么必须回读：Vela 里每个页面各自持有一份模块实例（各自的内存缓存），
// 记分页的缓存还停留在「删除之前」的 5 条；若直接用它写回，删掉的条目就会被写回去。
// 回读按版本戳取最新那份，所以晚写的删除结果一定赢。
export function addRecord(t, b, cb) {
  const entry = { t: t, b: b, ts: now() }
  loadRecords(function (list) {
    recordCache = normalize([[entry], list || []])
    flush()
    if (cb) cb(clone(recordCache))
  }, true)
}

// 删除一条：参数是**该条记录的时间戳**而不是下标。
// 用下标会在「列表页停留期间、记分页又存了一局」时删错条目；
// 时间戳来自当前渲染的那份数据，配合强制回读能定位到真正那一条。
export function removeRecord(ts, cb) {
  const run = function (list) {
    let idx = -1
    for (let i = 0; i < list.length; i++) {
      if ((list[i].ts || 0) === (ts || 0)) {
        idx = i
        break
      }
    }
    if (idx < 0) {
      if (cb) cb(clone(list))
      return
    }
    list.splice(idx, 1)
    saveRecords(list)
    if (cb) cb(clone(recordCache || list))
  }
  loadRecords(run, true)
}

// 诊断：两通道字符数 + 版本戳 + 内存条数
export function debugStats(cb) {
  readBoth(RECORD_KEY, RECORD_FILE, function (out) {
    const a = unpack(out.s)
    const b = unpack(out.f)
    cb({
      s: out.s === null ? 'null' : String(out.s).length,
      f: out.f === null ? 'null' : String(out.f).length,
      l: recordStamp,
      c: recordCache ? recordCache.length : -1,
      ds: a ? a.stamp : -1,
      df: b ? b.stamp : -1
    })
  })
}

export function pad2(n) {
  return n < 10 ? '0' + n : String(n)
}
