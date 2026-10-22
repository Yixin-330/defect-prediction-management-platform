<template>
  <div class="topbar">
    <div class="breadcrumb">
      <span v-for="(crumb, i) in breadcrumbs" :key="i" class="crumb-item">
        <span v-if="i > 0" class="crumb-sep">/</span>
        <span :class="{ 'crumb-active': i === breadcrumbs.length - 1 }">{{ crumb }}</span>
      </span>
    </div>
    <div class="topbar-right">
      <span class="demo-badge">原型演示 · 示例数据</span>
      <span class="icon-btn">🔔</span>
      <div class="user-info">
        <span class="user-avatar">林</span>
        <span class="user-name">林悦 · 团队成员</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const breadcrumbMap = {
  dashboard: ['团队项目', '校园协作平台', '项目工作台'],
  repo: ['团队项目', '校园协作平台', '仓库接入'],
  'commit-list': ['团队项目', '校园协作平台', '提交风险列表'],
  'commit-detail': ['团队项目', '校园协作平台', '提交风险列表', '提交详情'],
  'arrange-review': ['团队项目', '校园协作平台', '安排代码审查'],
  'review-list': ['团队项目', '校园协作平台', '审查处理记录'],
  'review-detail': ['团队项目', '校园协作平台', '审查处理记录', '详情'],
  trend: ['团队项目', '校园协作平台', '项目质量趋势']
}

const breadcrumbs = computed(() => breadcrumbMap[route.name] || ['团队项目'])
</script>

<style scoped>
.topbar {
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
}
.crumb-sep {
  margin: 0 4px;
  color: var(--text-tertiary);
}
.crumb-active {
  color: var(--text-primary);
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.demo-badge {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 2px 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
}
.icon-btn {
  cursor: pointer;
  font-size: 16px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: var(--color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 500;
}
.user-name {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>