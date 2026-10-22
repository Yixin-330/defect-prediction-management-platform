import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProjects } from '@/api/project'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      const res = await getProjects()
      projects.value = res.data || res || []
    } catch (e) {
      projects.value = []
    } finally {
      loading.value = false
    }
  }

  function setCurrentProject(project) {
    currentProject.value = project
  }

  return { projects, currentProject, loading, fetchProjects, setCurrentProject }
})