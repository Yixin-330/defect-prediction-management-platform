const DATASET_KEY = 'dpmp_datasets'
const MODEL_KEY = 'dpmp_models'

function read(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || '[]')
  } catch (e) {
    return []
  }
}

function write(key, list) {
  localStorage.setItem(key, JSON.stringify(list))
}

export function listDatasets() {
  return read(DATASET_KEY)
}

export function saveDataset(record) {
  const list = read(DATASET_KEY)
  const idx = list.findIndex(d => d.task_id === record.task_id)
  const item = { ...record, updated_at: new Date().toISOString() }
  if (idx >= 0) list[idx] = item
  else list.unshift(item)
  write(DATASET_KEY, list)
  return item
}

export function removeDataset(taskId) {
  const list = read(DATASET_KEY).filter(d => d.task_id !== taskId)
  write(DATASET_KEY, list)
}

export function listModels() {
  return read(MODEL_KEY)
}

export function saveModel(record) {
  const list = read(MODEL_KEY)
  const idx = list.findIndex(m => m.task_id === record.task_id)
  const item = { ...record, updated_at: new Date().toISOString() }
  if (idx >= 0) list[idx] = item
  else list.unshift(item)
  write(MODEL_KEY, list)
  return item
}

export function removeModel(taskId) {
  const list = read(MODEL_KEY).filter(m => m.task_id !== taskId)
  write(MODEL_KEY, list)
}