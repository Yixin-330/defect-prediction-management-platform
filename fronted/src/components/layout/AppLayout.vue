<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <TopBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  background-color: var(--bg-page);
}
</style>