<template>
  <aside class="sidebar">
    <div class="logo-area">
      <div class="logo-title">即时软件缺陷预测系统</div>
      <div class="logo-subtitle">开发团队 · 提交级风险分析</div>
    </div>

    <div class="project-selector">
      <div class="selector-label">当前项目</div>
      <div class="selector-value">
        <span>{{ projectStore.currentProject?.name || '校园协作平台' }}</span>
        <span class="selector-sub">{{ projectStore.currentProject?.group || '开发团队' }}</span>
      </div>
    </div>

    <nav class="nav-menu">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <p>预测辅助审查 · 不替代人工判断</p>
      <p class="footer-sub">🔒 团队数据隔离 · 加密存储</p>
    </div>
  </aside>
</template>

<script setup>
import { useProjectStore } from '@/stores/project'
import { useRoute } from 'vue-router'

const projectStore = useProjectStore()
const route = useRoute()

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path === path || route.path.startsWith(path + '/')
}

const navItems = [
  { path: '/', label: '项目工作台', icon: '◈' },
  { path: '/repo', label: '仓库接入', icon: '⬚' },
  { path: '/commits', label: '提交风险列表', icon: '▤' },
  { path: '/reviews', label: '审查处理记录', icon: '✓' },
  { path: '/trend', label: '项目质量趋势', icon: '📈' }
]
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  flex-shrink: 0;
}
.logo-area {
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border-color);
}
.logo-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.logo-subtitle {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}
.project-selector {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}
.selector-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}
.selector-value {
  display: flex;
  flex-direction: column;
  cursor: pointer;
}
.selector-value span:first-child {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}
.selector-sub {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.nav-menu {
  flex: 1;
  padding: 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 14px;
  transition: all 0.2s;
}
.nav-item:hover {
  background-color: var(--bg-card-hover);
  color: var(--text-primary);
}
.nav-item.active {
  background-color: var(--color-primary);
  color: #fff;
}
.nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--text-tertiary);
}
.footer-sub {
  margin-top: 2px;
}
</style>