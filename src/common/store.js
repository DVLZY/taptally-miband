// 数据层：比分与历史记录
// 双通道持久化：@system.storage（偏好存储）+ @system.file（应用私有文件）
// 读取时两处都读，任一处能解析出合法数据即可恢复。
//
// 关键设计（1.3.2 起）：所有数据在模块内有一份**内存缓存**。
//   - 写入：先更新缓存（同步、立即生效），再落盘；即使某次落盘/回读失败，本会话内也不会丢
//   - 读取：缓存已有值就直接用，不再依赖异步回读（回读在真机上偶发返回旧值会导致「只剩 1 条」）
//   - 落盘格式改成纯文本（逗号/分号分隔），不依赖 JSON，避免不同平台 JSON 实现差异

import storage from '@system.storage'
import file from '@system.file'

const SCORE_KEY = 'taptally_v1'
const SCORE_FILE = 'internal://files/taptally-score.txt'
const RECORD_KEY = 'taptally_records_v1'
const RECORD_FILE = 'internal://files/taptally-records.txt'
// 追加日志：每条记录单独 append 一行，写的时候不需要先读
// 这是「历史只剩 1 条」的根治手段——原实现每次都要「读全量→合并→覆盖写」，
// 只要那一次读取拿到旧值/空值，旧记录就被覆盖掉了；追加永不覆盖。
const RECORD_LOG = 'internal://files/taptally-records.log'

export const MAX_RECORDS = 5

// 版本号（页面里显示，用来确认手环上跑的到底是哪一版）
export const APP_VERSION = '1.5.0'

// 内存缓存
let scoreCache = null // { t, b }
let recordCache = null // [{ t, b, ts }]

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
// 三通道并行：追加日志 RECORD_LOG（只追加，不读即写）+ 偏好存储 + 整份文件
// 任一通道能读到就合并，按 (t,b,ts) 去重，时间倒序，取前 MAX_RECORDS 条
function parseRecords(raw) {
  if (!raw) return null
  const s = String(raw).trim()
  if (!s) return null
  // 日志每行一条、整份文件分号分隔，两种都吃（不用正则，避开转义坑）
  const nl = String.fromCharCode(10)
  const cr = String.fromCharCode(13)
  const segs = s.split(nl).join(';').split(cr).join(';').split(';').join(',').split(',')
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
  if (!out.length) return null
  return out
}

function serialize(list) {
  const segs = []
  for (let i = 0; i < list.length; i++) {
    segs.push(list[i].t + '-' + list[i].b + '-' + (list[i].ts || 0))
  }
  return segs.join(';')
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

// 读一条额外通道（日志用 readText，其余同 readBoth）
function readLog(cb) {
  try {
    file.readText({
      uri: RECORD_LOG,
      success: function (data) {
        cb(data && data.text ? String(data.text) : null)
      },
      fail: function () {
        cb(null)
      }
    })
  } catch (e) {
    cb(null)
  }
}

// 追加一行；append 不受支持时会退化成覆盖（那也只丢日志通道，另外两通道还在）
function appendLine(line) {
  try {
    file.writeText({ uri: RECORD_LOG, text: line + String.fromCharCode(10), append: true, fail: function () {} })
  } catch (e) {}
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
    const fromStore = parseRecords(out.s)
    const fromFile = parseRecords(out.f)
    readLog(function (logText) {
      const fromLog = parseRecords(logText)
      recordCache = normalize([recordCache, fromLog, fromStore, fromFile])
      cb(clone(recordCache))
    })
  })
}

export function saveRecords(list) {
  recordCache = normalize([list])
  const text = serialize(recordCache)
  writeBoth(RECORD_KEY, RECORD_FILE, text)
  // 删除/清空后必须把日志也重写成最终结果，否则下次合并会把删掉的条目捞回来
  try {
    file.writeText({ uri: RECORD_LOG, text: text ? text + String.fromCharCode(10) : '' })
  } catch (e) {}
}

// 新增一条：
//   1) 先 append 一行到日志（不需要读，绝不会覆盖旧记录）
//   2) 同步更新内存缓存并先写一次（本会话内立即生效）
//   3) 再异步把「日志 + 存储 + 文件」读回来的全量合并重写一次（跨页/跨会话也在）
// 旧实现是「读全量 → 合并 → 覆盖写」，页面第一次加记录时缓存还是空的，
// 读回来的可能只有 1 条，于是把历史覆盖成 1 条 —— 这就是「历史只剩 1 条」的根因。
export function addRecord(t, b, cb) {
  const entry = { t: t, b: b, ts: now() }
  appendLine(entry.t + '-' + entry.b + '-' + entry.ts)
  recordCache = normalize([[entry], recordCache || []])
  writeBoth(RECORD_KEY, RECORD_FILE, serialize(recordCache))
  const snapshot = clone(recordCache)
  if (cb) cb(snapshot)
  loadRecords(function (list) {
    recordCache = normalize([recordCache, list])
    writeBoth(RECORD_KEY, RECORD_FILE, serialize(recordCache))
  }, true)
}

// 删除第 idx 条
export function removeRecord(idx, cb) {
  loadRecords(function (list) {
    if (idx < 0 || idx >= list.length) {
      if (cb) cb(clone(list))
      return
    }
    list.splice(idx, 1)
    saveRecords(list)
    if (cb) cb(clone(list))
  })
}

// 诊断：三条通道各读到多少字符 + 内存条数，页面直接显示，用来定位「历史只有 1 条」
export function debugStats(cb) {
  readBoth(RECORD_KEY, RECORD_FILE, function (out) {
    readLog(function (logText) {
      cb({
        s: out.s === null ? 'null' : String(out.s).length,
        f: out.f === null ? 'null' : String(out.f).length,
        l: logText === null ? 'null' : String(logText).length,
        c: recordCache ? recordCache.length : -1
      })
    })
  })
}

function now() {
  try {
    return Date.now() || 0
  } catch (e) {
    return 0
  }
}

export function pad2(n) {
  return n < 10 ? '0' + n : String(n)
}

// 时间戳 -> "21:05"；拿不到时间返回空串
export function formatTime(ts) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return pad2(d.getHours()) + ':' + pad2(d.getMinutes())
  } catch (e) {
    return ''
  }
}
