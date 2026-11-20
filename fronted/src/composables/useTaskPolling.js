import { ref, onUnmounted } from 'vue'
import { getTaskStatus } from '@/api/task'

export function useTaskPolling(intervalMs = 1500) {
  const taskState = ref(null)
  const polling = ref(false)
  let timer = null

  function stop() {
    polling.value = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  async function poll(taskId, onDone) {
    if (!taskId) return
    polling.value = true
    try {
      const res = await getTaskStatus(taskId)
      taskState.value = res
      const status = (res && (res.status || res.state)) || ''
      if (status === 'success' || status === 'failed' || status === 'error') {
        stop()
        if (onDone) onDone(res)
        return
      }
    } catch (e) {
      stop()
      taskState.value = { status: 'failed', message: (e && e.message) || '任务查询失败' }
      if (onDone) onDone(taskState.value)
      return
    }
    timer = setInterval(async () => {
      try {
        const res = await getTaskStatus(taskId)
        taskState.value = res
        const status = (res && (res.status || res.state)) || ''
        if (status === 'success' || status === 'failed' || status === 'error') {
          stop()
          if (onDone) onDone(res)
        }
      } catch (e) {
        stop()
        taskState.value = { status: 'failed', message: (e && e.message) || '任务查询失败' }
        if (onDone) onDone(taskState.value)
      }
    }, intervalMs)
  }

  onUnmounted(stop)

  return { taskState, polling, poll, stop }
}