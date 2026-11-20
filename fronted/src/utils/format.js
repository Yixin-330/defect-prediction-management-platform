import dayjs from 'dayjs'

export function formatDateTime(dt) {
  if (!dt) return '-'
  return dayjs(dt).format('YYYY-MM-DD HH:mm')
}

export function formatDate(dt) {
  if (!dt) return '-'
  return dayjs(dt).format('YYYY-MM-DD')
}

export function formatShortDateTime(dt) {
  if (!dt) return '-'
  return dayjs(dt).format('MM/DD HH:mm')
}

export function riskLevel(score) {
  if (score == null) return 'none'
  if (score >= 0.7) return 'high'
  if (score >= 0.4) return 'mid'
  return 'low'
}

export function levelFromBackend(level) {
  const map = { '高': 'high', '中': 'mid', '低': 'low' }
  return map[level] || 'none'
}

export function statusFromBackend(status) {
  const map = { '待审查': 'waiting', '处理中': 'reviewing', '已处理': 'done', '已忽略': 'ignored' }
  return map[status] || status
}

export function buildTrendFromBackend(riskTrend) {
  if (!riskTrend || !riskTrend.length) return []
  return riskTrend.map(item => ({
    date: item.date ? item.date.slice(5, 10) : '未知',
    high: item.risk_count || 0,
    mid: 0,
    low: 0
  }))
}

export function buildTrendFromPredictions(predictions) {
  if (!predictions || !predictions.length) return []
  const grouped = {}
  for (const p of predictions) {
    const date = p.predicted_at ? p.predicted_at.slice(5, 10) : '未知'
    if (!grouped[date]) grouped[date] = { date, high: 0, mid: 0, low: 0 }
    if (p.level === '高') grouped[date].high++
    else if (p.level === '中') grouped[date].mid++
    else if (p.level === '低') grouped[date].low++
  }
  return Object.values(grouped).sort((a, b) => a.date.localeCompare(b.date))
}

export function buildTrendFromCommits(commits) {
  if (!commits || !commits.length) return []
  const grouped = {}
  for (const c of commits) {
    const date = c.date ? c.date.slice(5, 10) : '未知'
    if (!grouped[date]) grouped[date] = { date, high: 0, mid: 0, low: 0 }
    const msg = (c.message || '').toLowerCase()
    if (msg.includes('fix') || msg.includes('bug')) {
      grouped[date].high++
    } else if ((c.message || '').length < 10) {
      grouped[date].mid++
    } else {
      grouped[date].low++
    }
  }
  return Object.values(grouped).sort((a, b) => a.date.localeCompare(b.date))
}

export function riskLabel(level) {
  const map = { high: '高风险', mid: '中风险', low: '低风险', none: '无评分' }
  return map[level] || '无评分'
}

export function priorityLabel(score) {
  if (score == null) return '—'
  if (score >= 0.7) return '优先'
  return '常规'
}

export function predictStatusLabel(status) {
  const map = {
    completed: '已完成',
    analyzing: '分析中',
    failed: '预测失败',
    pending: '待预测'
  }
  return map[status] || status
}

export function reviewStatusLabel(status) {
  const map = {
    pending: '待分配',
    waiting: '待审查',
    reviewing: '审查中',
    rechecking: '待复核',
    done: '已完成',
    ignored: '已忽略'
  }
  return map[status] || status
}