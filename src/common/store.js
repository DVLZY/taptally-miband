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

export const MAX_RECORDS = 5

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
// 落盘格式："12-9-1699000000000;7-11-1699000000001"
function parseRecords(raw) {
  if (!raw) return null
  const s = String(raw).trim()
  if (!s) return null
  const segs = s.split(';')
  const out = []
  for (let i = 0; i < segs.length; i++) {
    const seg = segs[i].trim()
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

export function loadRecords(cb, force) {
  if (recordCache && !force) {
    const c = clone(recordCache)
    later(function () {
      cb(c)
    })
    return
  }
  readBoth(RECORD_KEY, RECORD_FILE, function (out) {
    const disk = parseRecords(out.s) || parseRecords(out.f)
    // force 回读时：磁盘为空但缓存有数据，说明回读不可靠，保留缓存
    if (disk && (disk.length >= (recordCache ? recordCache.length : 0))) {
      recordCache = clone(disk)
    } else if (!recordCache) {
      recordCache = []
    }
    cb(clone(recordCache))
  })
}

export function saveRecords(list) {
  recordCache = clone(list)
  writeBoth(RECORD_KEY, RECORD_FILE, serialize(list))
}

// 新增一条：最新在前，最多 MAX_RECORDS 条
export function addRecord(t, b, cb) {
  loadRecords(function (list) {
    const next = [{ t: t, b: b, ts: now() }]
    for (let i = 0; i < list.length && i < MAX_RECORDS - 1; i++) {
      next.push(list[i])
    }
    saveRecords(next)
    if (cb) cb(clone(next))
  })
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
