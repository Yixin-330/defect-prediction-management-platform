import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/Dashboard.vue'), meta: { title: '项目工作台' } },
      { path: 'repo', name: 'repo', component: () => import('@/views/RepoConnect.vue'), meta: { title: '仓库接入' } },
      { path: 'commits', name: 'commit-list', component: () => import('@/views/CommitRiskList.vue'), meta: { title: '提交风险列表' } },
      { path: 'commits/:id', name: 'commit-detail', component: () => import('@/views/CommitDetail.vue'), meta: { title: '提交详情与风险解释' } },
      { path: 'commits/:id/arrange', name: 'arrange-review', component: () => import('@/views/ArrangeReview.vue'), meta: { title: '安排代码审查' } },
      { path: 'reviews', name: 'review-list', component: () => import('@/views/ReviewRecord.vue'), meta: { title: '审查处理记录' } },
      { path: 'reviews/:id', name: 'review-detail', component: () => import('@/views/ReviewRecord.vue'), meta: { title: '审查处理记录' } },
      { path: 'trend', name: 'trend', component: () => import('@/views/QualityTrend.vue'), meta: { title: '项目质量趋势' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 即时软件缺陷预测系统` : '即时软件缺陷预测系统'
})

export default router