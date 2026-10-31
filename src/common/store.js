// 数据层：比分与历史记录
// 双通道持久化：@system.storage（偏好存储）+ @system.file（应用私有文件）
// 读取时两处都读，任一处能解析出合法数据即可恢复。

import storage from '@system.storage'
import file from '@system.file'

const SCORE_KEY = 'taptally_v1'
const SCORE_FILE = 'internal://files/taptally-score.txt'
const RECORD_KEY = 'taptally_records_v1'
const RECORD_FILE = 'internal://files/taptally-records.txt'

export const MAX_RECORDS = 10

// 列表页恢复比分后，通知记分页重新读一次
let refreshFlag = false

export function requestScoreRefresh() {
  refreshFlag = true
}

export function consumeScoreRefresh() {
  const v = refreshFlag
  refreshFlag = false
  return v
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

// 后备：把文件写入到 txt 文件；读取时先看存储再看文件
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
  writeBoth(SCORE_KEY, SCORE_FILE, t + '-' + b)
}

export function loadScore(cb) {
  readBoth(SCORE_KEY, SCORE_FILE, function (out) {
    cb(parseScore(out.s) || parseScore(out.f))
  })
}

// ---------- 历史记录 ----------
// 存储格式：[[t, b, ts], ...]，最新在前
function parseRecords(raw) {
  if (!raw) return null
  let arr = null
  try {
    arr = JSON.parse(String(raw))
  } catch (e) {
    return null
  }
  if (!arr || typeof arr.length !== 'number') return null
  const out = []
  for (let i = 0; i < arr.length; i++) {
    const it = arr[i]
    if (!it || typeof it.length !== 'number' || it.length < 2) continue
    const t = parseInt(it[0], 10)
    const b = parseInt(it[1], 10)
    const ts = parseInt(it[2], 10)
    if (isNaN(t) || isNaN(b)) continue
    out.push({ t: t, b: b, ts: isNaN(ts) ? 0 : ts })
  }
  return out
}

function serialize(list) {
  const arr = []
  for (let i = 0; i < list.length; i++) {
    arr.push([list[i].t, list[i].b, list[i].ts || 0])
  }
  return JSON.stringify(arr)
}

export function loadRecords(cb) {
  readBoth(RECORD_KEY, RECORD_FILE, function (out) {
    cb(parseRecords(out.s) || parseRecords(out.f) || [])
  })
}

export function saveRecords(list) {
  writeBoth(RECORD_KEY, RECORD_FILE, serialize(list))
}

// 新增一条：最新在前，最多 MAX_RECORDS 条
export function addRecord(t, b, cb) {
  loadRecords(function (list) {
    const next = [{ t: t, b: b, ts: Date.now() }]
    for (let i = 0; i < list.length && i < MAX_RECORDS - 1; i++) {
      next.push(list[i])
    }
    saveRecords(next)
    if (cb) cb(next)
  })
}

// 删除第 idx 条
export function removeRecord(idx, cb) {
  loadRecords(function (list) {
    if (idx < 0 || idx >= list.length) {
      if (cb) cb(list)
      return
    }
    list.splice(idx, 1)
    saveRecords(list)
    if (cb) cb(list)
  })
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
