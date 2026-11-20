import { getProjects, registerProject, getDashboardSummary, getRiskRanking, getRepoCommits } from '@/api/project'
import { getPrediction } from '@/api/prediction'

export async function ensureProject(repoUrl = '') {
  const projects = await getProjects()
  if (projects && projects.length > 0) return projects[0]
  const project = await registerProject({
    name: '默认项目',
    git_url: repoUrl,
    owner: '开发团队',
    description: '自动创建'
  })
  return project
}

export async function generatePredictionsForCommits(commits) {
  const results = []
  for (const commit of commits) {
    try {
      const pred = await getPrediction(commit.id)
      results.push({
        commit_id: commit.id,
        commit_hash: commit.hash,
        risk_score: pred.risk_score,
        level: pred.level
      })
    } catch (e) {
      // skip failed prediction
    }
  }
  results.sort((a, b) => b.risk_score - a.risk_score)
  return results
}

export async function ensureProjectAndPredictions(repoId, repoUrl = '') {
  const project = await ensureProject(repoUrl)
  const repoData = await getRepoCommits(repoId)
  const commits = repoData.commits || []
  await generatePredictionsForCommits(commits)
  return { project, commitCount: commits.length }
}

export async function getRankingWithFallback(projectId = null) {
  const summary = await getDashboardSummary()
  const projects = await getProjects()
  const project = projectId
    ? (projects || []).find(p => p.id === projectId)
    : (projects || [])[0]

  if (project) {
    const ranking = await getRiskRanking(project.id)
    if (ranking.items && ranking.items.length > 0) {
      return { items: ranking.items, project, summary, projects }
    }
  }

  const commits = summary.recent_commits || []
  if (commits.length === 0) {
    return { items: [], project: project || null, summary, projects }
  }

  const items = await generatePredictionsForCommits(commits)

  if (project) {
    const ranking = await getRiskRanking(project.id)
    if (ranking.items && ranking.items.length > 0) {
      return { items: ranking.items, project, summary, projects }
    }
  }

  return { items, project: project || null, summary, projects }
}