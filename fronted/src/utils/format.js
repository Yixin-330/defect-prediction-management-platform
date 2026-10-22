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